import { Link } from 'react-router-dom'
import { Button } from '../components/ui/Button'
import { Card, CardContent } from '../components/ui/Card'
import {
  Code2,
  BarChart3,
  Trophy,
  Target,
  TrendingUp,
  Users,
  ArrowRight,
} from 'lucide-react'

export default function Landing() {
  const features = [
    {
      icon: Code2,
      title: 'Multi-Platform Integration',
      description: 'Connect LeetCode, Codeforces, CodeChef, GitHub and more in one place.',
    },
    {
      icon: BarChart3,
      title: 'Comprehensive Analytics',
      description: 'Track your progress with detailed statistics and visualizations.',
    },
    {
      icon: Trophy,
      title: 'Contest Tracking',
      description: 'Monitor your contest performance and rating progression.',
    },
    {
      icon: Target,
      title: 'Streak Tracking',
      description: 'Stay consistent with daily coding streak monitoring.',
    },
    {
      icon: TrendingUp,
      title: 'Progress Insights',
      description: 'Understand your strengths and areas for improvement.',
    },
    {
      icon: Users,
      title: 'Public Portfolio',
      description: 'Showcase your coding journey with a shareable profile.',
    },
  ]

  return (
    <div className="min-h-screen bg-gradient-to-b from-background via-primary/5 to-background">
      {/* Navbar */}
      <nav className="border-b bg-card/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
              <Code2 className="h-5 w-5 text-primary-foreground" />
            </div>
            <span className="text-xl font-bold">DevAnalytics</span>
          </div>
          <div className="flex items-center gap-4">
            <Link to="/login">
              <Button variant="ghost">Login</Button>
            </Link>
            <Link to="/login">
              <Button>Get Started</Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-20 text-center">
        <div className="max-w-3xl mx-auto space-y-6">
          <h1 className="text-5xl md:text-6xl font-bold tracking-tight">
            Track Your{' '}
            <span className="text-primary">Coding Journey</span>
          </h1>
          <p className="text-xl text-muted-foreground">
            Aggregate your coding profiles, visualize your progress, and showcase
            your achievements all in one beautiful dashboard.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center pt-4">
            <Link to="/login">
              <Button size="lg" className="w-full sm:w-auto">
                Sign In
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
            <Button size="lg" variant="outline" className="w-full sm:w-auto">
              View Demo
            </Button>
          </div>
        </div>

        {/* Preview Image/Chart */}
        <div className="mt-16 max-w-5xl mx-auto">
          <Card className="overflow-hidden shadow-2xl">
            <CardContent className="p-0">
              <div className="aspect-video bg-gradient-to-br from-primary/20 to-secondary/20 flex items-center justify-center">
                <BarChart3 className="h-32 w-32 text-primary/40" />
              </div>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Features Section */}
      <section className="container mx-auto px-4 py-20">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Everything You Need to Track Progress
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Powerful features to help you stay motivated and improve your coding skills.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, index) => (
            <Card key={index} className="hover:shadow-lg transition-shadow">
              <CardContent className="p-6">
                <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                  <feature.icon className="h-6 w-6 text-primary" />
                </div>
                <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
                <p className="text-muted-foreground">{feature.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* CTA Section */}
      <section className="container mx-auto px-4 py-20">
        <Card className="bg-primary text-primary-foreground">
          <CardContent className="p-12 text-center">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Ready to Level Up Your Coding?
            </h2>
            <p className="text-lg mb-8 opacity-90">
              Join thousands of developers tracking their progress with DevAnalytics.
            </p>
            <Link to="/login">
              <Button size="lg" variant="secondary">
                Sign In to Your Account
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
          </CardContent>
        </Card>
      </section>

      {/* Footer */}
      <footer className="border-t bg-card/50 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-8">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="flex items-center gap-2">
              <Code2 className="h-5 w-5 text-primary" />
              <span className="font-semibold">DevAnalytics</span>
            </div>
            <p className="text-sm text-muted-foreground">
              © 2024 DevAnalytics. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}
