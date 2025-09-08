export default function TermsPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gray-900 text-gray-300 p-8">
      <div className="max-w-4xl w-full text-center space-y-6">
        <h1 className="text-4xl sm:text-5xl font-bold text-white">
          Conditions d'Utilisation
        </h1>
        <div className="text-lg text-gray-400 space-y-4">
          <p>L’accès au site Gaming Advisor vaut acceptation des présentes conditions.</p>

          <div>
            <h2 className="text-2xl font-semibold text-white mt-8 mb-2">Accès au service</h2>
            <p>L'accès au chatbot nécessite une inscription et est réservé à un usage personnel dans le cadre de ce projet éducatif.</p>
          </div>

          <div>
            <h2 className="text-2xl font-semibold text-white mt-8 mb-2">Limitation de responsabilité</h2>
            <p>Gaming Advisor est un projet éducatif. Les informations fournies sont données à titre indicatif et ne sauraient engager la responsabilité de l'éditeur.</p>
          </div>
        </div>
      </div>
    </div>
  );
}