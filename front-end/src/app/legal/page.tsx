export default function LegalPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gray-900 text-gray-300 p-8">
      <div className="max-w-4xl w-full text-center space-y-6">
        <h1 className="text-4xl sm:text-5xl font-bold text-white">
          Mentions Légales
        </h1>
        <div className="text-lg text-gray-400 space-y-4">
          <p>Conformément aux dispositions de la loi pour la confiance en l'économie numérique, voici les informations de l'éditeur du site Gaming Advisor.</p>

          <div>
            <h2 className="text-2xl font-semibold text-white mt-8 mb-2">Édition du site</h2>
            <p>Gaming Advisor</p>
          </div>

          <div>
            <h2 className="text-2xl font-semibold text-white mt-8 mb-2">Hébergement</h2>
            <p>Le site est hébergé par Microsoft Azure.</p>
          </div>

          <div>
            <h2 className="text-2xl font-semibold text-white mt-8 mb-2">Nous contacter</h2>
            <p>Par email : contact@gamingadvisor.fr</p>
          </div>
        </div>
      </div>
    </div>
  );
}