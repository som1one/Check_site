import Header from '@/components/ui/Header'
import Footer from '@/components/ui/Footer'
import HeroSection from '@/components/sections/HeroSection'
import HowItWorksSection from '@/components/sections/HowItWorksSection'
import ChecksSection from '@/components/sections/ChecksSection'
import ExampleReportSection from '@/components/sections/ExampleReportSection'
import PricingSection from '@/components/sections/PricingSection'
import FAQSection from '@/components/sections/FAQSection'

export default function HomePage() {
  return (
    <>
      <Header />
      <main>
        <HeroSection />
        <HowItWorksSection />
        <ChecksSection />
        <ExampleReportSection />
        <PricingSection />
        <FAQSection />
      </main>
      <Footer />
    </>
  )
}
