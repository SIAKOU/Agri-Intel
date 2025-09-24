# Script de génération automatique du frontend AgriIntel360
# Usage: .\scripts\generate-frontend.ps1

Write-Host "🎨 Génération automatique du frontend AgriIntel360" -ForegroundColor Green

$FrontendPath = "S:\Agri intel 360\frontend\src"

# Fonction pour créer un fichier avec contenu
function New-FileWithContent {
    param(
        [string]$Path,
        [string]$Content
    )
    
    $dir = Split-Path $Path -Parent
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    
    $Content | Out-File -FilePath $Path -Encoding UTF8
    Write-Host "  ✅ Créé: $(Split-Path $Path -Leaf)" -ForegroundColor Green
}

Write-Host "`n📁 Création de la structure des composants..." -ForegroundColor Yellow

# 1. Page d'accueil avec hero section
$HomePage = @"
'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  Leaf, 
  BarChart3, 
  MapPin, 
  Brain, 
  TrendingUp, 
  Globe, 
  Users, 
  AlertTriangle,
  ArrowRight,
  Play
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import Link from 'next/link'

const stats = [
  { label: 'Pays Couverts', value: '15+', icon: Globe },
  { label: 'Utilisateurs Actifs', value: '10K+', icon: Users },
  { label: 'Prédictions', value: '99.2%', icon: Brain },
  { label: 'Données Traitées', value: '2.5M', icon: BarChart3 },
]

const features = [
  {
    icon: BarChart3,
    title: 'Tableaux de Bord Intelligents',
    description: 'Visualisez vos données agricoles en temps réel avec des graphiques interactifs et des KPIs personnalisés.',
  },
  {
    icon: Brain,
    title: 'IA & Prédictions',
    description: 'Algorithmes d\'apprentissage automatique pour prédire les rendements, prix et conditions météorologiques.',
  },
  {
    icon: MapPin,
    title: 'Cartes Géospatiales',
    description: 'Analysez vos données sur des cartes interactives avec géolocalisation et couches thématiques.',
  },
  {
    icon: AlertTriangle,
    title: 'Alertes Intelligentes',
    description: 'Recevez des notifications en temps réel sur les conditions critiques et opportunités de marché.',
  },
]

export default function HomePage() {
  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-br from-agri-50 via-white to-agri-50 pt-20 pb-16">
        <div className="absolute inset-0 bg-agri-pattern opacity-5" />
        <div className="container mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="text-center max-w-4xl mx-auto"
          >
            <div className="flex items-center justify-center mb-6">
              <Leaf className="h-12 w-12 text-agri-600 mr-3" />
              <h1 className="text-5xl md:text-7xl font-bold gradient-text">
                AgriIntel360
              </h1>
            </div>
            
            <p className="text-xl md:text-2xl text-muted-foreground mb-8 max-w-3xl mx-auto leading-relaxed">
              Transformez vos décisions agricoles avec l'intelligence artificielle. 
              <span className="text-agri-600 font-semibold"> Analysez, prédisez, optimisez </span>
              vos rendements en temps réel.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
              <Button size="lg" className="text-lg px-8 py-6" asChild>
                <Link href="/dashboard">
                  Commencer Maintenant
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Link>
              </Button>
              
              <Button variant="outline" size="lg" className="text-lg px-8 py-6">
                <Play className="mr-2 h-5 w-5" />
                Voir la Démo
              </Button>
            </div>
            
            {/* Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 max-w-3xl mx-auto">
              {stats.map((stat, index) => (
                <motion.div
                  key={stat.label}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.8, delay: index * 0.1 }}
                  className="text-center"
                >
                  <stat.icon className="h-8 w-8 text-agri-600 mx-auto mb-2" />
                  <div className="text-3xl font-bold text-foreground">{stat.value}</div>
                  <div className="text-sm text-muted-foreground">{stat.label}</div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-background">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold mb-4">
              Une Plateforme Complète pour l'Agriculture Moderne
            </h2>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              Découvrez nos fonctionnalités avancées conçues spécialement pour l'agriculture africaine
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: index * 0.1 }}
                viewport={{ once: true }}
              >
                <Card className="p-6 h-full card-hover">
                  <feature.icon className="h-12 w-12 text-agri-600 mb-4" />
                  <h3 className="text-xl font-semibold mb-3">{feature.title}</h3>
                  <p className="text-muted-foreground">{feature.description}</p>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-agri-600 text-white">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-4xl font-bold mb-4">
            Prêt à Révolutionner Votre Agriculture ?
          </h2>
          <p className="text-xl opacity-90 mb-8 max-w-2xl mx-auto">
            Rejoignez des milliers d'agriculteurs qui utilisent déjà AgriIntel360 pour optimiser leurs rendements
          </p>
          <Button size="lg" variant="secondary" className="text-lg px-8 py-6" asChild>
            <Link href="/auth/register">
              Créer un Compte Gratuit
              <ArrowRight className="ml-2 h-5 w-5" />
            </Link>
          </Button>
        </div>
      </section>
    </div>
  )
}
"@

New-FileWithContent -Path "$FrontendPath\app\page.tsx" -Content $HomePage

# 2. Composants UI supplémentaires
$Card = @"
import * as React from "react"
import { cn } from "@/lib/utils"

const Card = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      "rounded-lg border bg-card text-card-foreground shadow-sm",
      className
    )}
    {...props}
  />
))
Card.displayName = "Card"

const CardHeader = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex flex-col space-y-1.5 p-6", className)}
    {...props}
  />
))
CardHeader.displayName = "CardHeader"

const CardTitle = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h3
    ref={ref}
    className={cn(
      "text-2xl font-semibold leading-none tracking-tight",
      className
    )}
    {...props}
  />
))
CardTitle.displayName = "CardTitle"

const CardDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={cn("text-sm text-muted-foreground", className)}
    {...props}
  />
))
CardDescription.displayName = "CardDescription"

const CardContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn("p-6 pt-0", className)} {...props} />
))
CardContent.displayName = "CardContent"

const CardFooter = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex items-center p-6 pt-0", className)}
    {...props}
  />
))
CardFooter.displayName = "CardFooter"

export { Card, CardHeader, CardFooter, CardTitle, CardDescription, CardContent }
"@

New-FileWithContent -Path "$FrontendPath\components\ui\card.tsx" -Content $Card

# 3. Providers
$ThemeProvider = @"
'use client'

import * as React from "react"
import { ThemeProvider as NextThemesProvider } from "next-themes"
import { type ThemeProviderProps } from "next-themes/dist/types"

export function ThemeProvider({ children, ...props }: ThemeProviderProps) {
  return <NextThemesProvider {...props}>{children}</NextThemesProvider>
}
"@

New-FileWithContent -Path "$FrontendPath\components\providers\theme-provider.tsx" -Content $ThemeProvider

$QueryProvider = @"
'use client'

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { useState } from 'react'

export function QueryProvider({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000,
            refetchOnWindowFocus: false,
          },
        },
      })
  )

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  )
}
"@

New-FileWithContent -Path "$FrontendPath\components\providers\query-provider.tsx" -Content $QueryProvider

$AuthProvider = @"
'use client'

import { createContext, useContext, useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'

interface User {
  id: string
  email: string
  username: string
  full_name: string
  role: string
}

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const router = useRouter()

  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = async () => {
    try {
      const token = localStorage.getItem('token')
      if (token) {
        const response = await fetch('/api/v1/auth/me', {
          headers: { Authorization: `Bearer ${token}` },
        })
        if (response.ok) {
          const userData = await response.json()
          setUser(userData)
        } else {
          localStorage.removeItem('token')
        }
      }
    } catch (error) {
      console.error('Auth check failed:', error)
    } finally {
      setLoading(false)
    }
  }

  const login = async (username: string, password: string) => {
    const response = await fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    })

    if (!response.ok) {
      throw new Error('Login failed')
    }

    const data = await response.json()
    localStorage.setItem('token', data.access_token)
    setUser(data.user)
    router.push('/dashboard')
  }

  const logout = () => {
    localStorage.removeItem('token')
    setUser(null)
    router.push('/')
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
"@

New-FileWithContent -Path "$FrontendPath\components\providers\auth-provider.tsx" -Content $AuthProvider

$ToasterProvider = @"
'use client'

import { Toaster } from 'react-hot-toast'

export function ToasterProvider() {
  return (
    <Toaster
      position="top-right"
      toastOptions={{
        duration: 4000,
        style: {
          background: 'hsl(var(--card))',
          color: 'hsl(var(--card-foreground))',
          border: '1px solid hsl(var(--border))',
        },
      }}
    />
  )
}
"@

New-FileWithContent -Path "$FrontendPath\components\providers\toaster-provider.tsx" -Content $ToasterProvider

Write-Host "`n🎨 Composants de base créés avec succès!" -ForegroundColor Green
Write-Host "📋 Prochaines étapes:" -ForegroundColor Yellow
Write-Host "  1. Installer les dépendances: cd frontend && npm install" -ForegroundColor White
Write-Host "  2. Créer les composants de dashboard" -ForegroundColor White
Write-Host "  3. Intégrer les visualisations de données" -ForegroundColor White
Write-Host "  4. Ajouter l'authentification" -ForegroundColor White

Write-Host "`n✅ Frontend partiellement généré!" -ForegroundColor Green