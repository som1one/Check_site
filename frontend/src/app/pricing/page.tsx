import Header from '@/components/ui/Header'
import Footer from '@/components/ui/Footer'
import PricingSection from '@/components/sections/PricingSection'

export default function PricingPage() {
  return (
    <>
      <Header />
      <main>
        <div className="bg-white py-16 text-center border-b border-slate-100">
          <div className="max-w-2xl mx-auto px-4">
            <h1 className="text-4xl font-bold text-slate-900 mb-4">Тарифы SiteGuard</h1>
            <p className="text-lg text-slate-500">
              Выберите подходящий план. Начните бесплатно — без регистрации и карты.
            </p>
          </div>
        </div>
        <PricingSection />
      </main>
      <Footer />
    </>
  )
}
