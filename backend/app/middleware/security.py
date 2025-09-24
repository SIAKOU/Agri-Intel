"""
Security middleware for FastAPI
"""

import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to responses"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Security headers
        security_headers = {
            # Prevent clickjacking
            "X-Frame-Options": "DENY",
            
            # Prevent MIME sniffing
            "X-Content-Type-Options": "nosniff",
            
            # Enable XSS protection
            "X-XSS-Protection": "1; mode=block",
            
            # Referrer policy
            "Referrer-Policy": "strict-origin-when-cross-origin",
            
            # Content Security Policy
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "connect-src 'self' https:; "
                "font-src 'self' https:; "
                "object-src 'none'; "
                "base-uri 'self'; "
                "form-action 'self';"
            ),
            
            # Strict Transport Security (HTTPS only)
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            
            # Permissions Policy
            "Permissions-Policy": (
                "geolocation=(), microphone=(), camera=(), "
                "payment=(), usb=(), magnetometer=(), gyroscope=(), "
                "accelerometer=(), ambient-light-sensor=(), autoplay=()"
            ),
            
            # Hide server information
            "Server": "AgriIntel360",
            
            # Cache control for sensitive endpoints
            "Cache-Control": "no-cache, no-store, must-revalidate" if "/api/" in str(request.url) else "public, max-age=3600",
            "Pragma": "no-cache" if "/api/" in str(request.url) else "",
        }
        
        # Add security headers
        for header, value in security_headers.items():
            if value:  # Only add non-empty headers
                response.headers[header] = value
        
        # Remove sensitive headers in production
        response.headers.pop("server", None)
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware"""
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.clients = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get client IP
        client_ip = request.client.host
        
        # Skip rate limiting for health checks and internal IPs
        if (
            request.url.path.startswith("/health") or
            client_ip in ["127.0.0.1", "::1", "localhost"] or
            client_ip.startswith("10.") or
            client_ip.startswith("192.168.") or
            (client_ip.startswith("172.") and 16 <= int(client_ip.split(".")[1]) <= 31)
        ):
            return await call_next(request)
        
        current_time = time.time()
        
        # Initialize or update client data
        if client_ip not in self.clients:
            self.clients[client_ip] = []
        
        # Remove old requests (older than 1 minute)
        self.clients[client_ip] = [
            req_time for req_time in self.clients[client_ip]
            if current_time - req_time < 60
        ]
        
        # Check rate limit
        if len(self.clients[client_ip]) >= self.requests_per_minute:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later."
            )
        
        # Add current request
        self.clients[client_ip].append(current_time)
        
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(
            self.requests_per_minute - len(self.clients[client_ip])
        )
        response.headers["X-RateLimit-Reset"] = str(int(current_time + 60))
        
        return response


class CORSSecurityMiddleware(BaseHTTPMiddleware):
    """Enhanced CORS security middleware"""
    
    def __init__(self, app, allowed_origins: list = None):
        super().__init__(app)
        self.allowed_origins = allowed_origins or []
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        origin = request.headers.get("origin")
        
        # Check if origin is allowed
        if origin and self.allowed_origins and origin not in self.allowed_origins:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Origin not allowed"
            )
        
        response = await call_next(request)
        
        # Add CORS headers for allowed origins
        if origin and (not self.allowed_origins or origin in self.allowed_origins):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = (
                "Authorization, Content-Type, Accept, Origin, User-Agent, "
                "Cache-Control, X-Requested-With"
            )
            response.headers["Access-Control-Max-Age"] = "86400"  # 24 hours
        
        return response


class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """CSRF protection middleware"""
    
    def __init__(self, app, exempt_paths: list = None):
        super().__init__(app)
        self.exempt_paths = exempt_paths or ["/health", "/docs", "/openapi.json"]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip CSRF protection for exempt paths and safe methods
        if (
            any(request.url.path.startswith(path) for path in self.exempt_paths) or
            request.method in ["GET", "HEAD", "OPTIONS"]
        ):
            return await call_next(request)
        
        # Check for CSRF token in headers
        csrf_token = request.headers.get("X-CSRF-Token")
        
        # For now, we'll implement a simple origin check
        # In production, use proper CSRF tokens
        origin = request.headers.get("origin")
        referer = request.headers.get("referer")
        
        # Require origin or referer for state-changing requests
        if not origin and not referer:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF protection: Origin or Referer required"
            )
        
        return await call_next(request)