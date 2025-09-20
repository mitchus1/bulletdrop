export default function Home() {
  return (
    <div className="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Discord Profiles & Image Hosting
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          Create stunning Discord-style profiles and host your screenshots with custom domains
        </p>
        <div className="space-x-4">
          <a
            href="/register"
            className="bg-blue-600 text-white px-6 py-3 rounded-lg text-lg hover:bg-blue-700"
          >
            Get Started
          </a>
          <a
            href="/login"
            className="border border-gray-300 text-gray-700 px-6 py-3 rounded-lg text-lg hover:bg-gray-50"
          >
            Sign In
          </a>
        </div>
      </div>
    </div>
  )
}