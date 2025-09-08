export default function PrivacyPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gray-900 text-gray-300 p-8">
      <div className="max-w-4xl w-full text-center space-y-6">
        <h1 className="text-4xl sm:text-5xl font-bold text-white">
          Politique de Confidentialité
        </h1>
        <div className="text-lg text-gray-400 space-y-4">
          <p>Cette politique de confidentialité décrit comment Gaming Advisor utilise et protège les informations que vous donnez lorsque vous utilisez ce site.</p>

          <div>
            <h2 className="text-2xl font-semibold text-white mt-8 mb-2">Données collectées</h2>
            <p>Nous collectons les informations suivantes lors de votre inscription : Nom, prénom, nom d'utilisateur et adresse e-mail.</p>
          </div>

          <div>
            <h2 className="text-2xl font-semibold text-white mt-8 mb-2">Finalité des données</h2>
            <p>Ces informations sont nécessaires pour la gestion de votre compte, la fourniture du service et sa sécurisation.</p>
          </div>

          <div>
            <h2 className="text-2xl font-semibold text-white mt-8 mb-2">Vos droits</h2>
            <p>Conformément au RGPD, vous disposez d'un droit d'accès, de rectification, et de suppression de vos données personnelles.</p>
          </div>
        </div>
      </div>
    </div>
  );
}