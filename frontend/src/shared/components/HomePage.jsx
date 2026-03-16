function HomePage() {
    return (
      <div className="min-h-screen bg-gradient-to-br from-teal-900 via-blue-900 to-indigo-900 text-white overflow-hidden">
        {/* Hero Section */}
        <section className="relative pt-24 pb-20 md:pt-32 md:pb-28">
          <div className="container mx-auto px-6">
            <div className="flex flex-col lg:flex-row items-center gap-12">
              {/* Left Text */}
              <div className="lg:w-1/2">
                <h1 className="text-5xl md:text-7xl lg:text-8xl font-black bg-gradient-to-r from-green-400 to-teal-400 bg-clip-text text-transparent mb-6 leading-tight">
                  Stock Market
                </h1>
                <h2 className="text-3xl md:text-4xl font-bold text-white/90 mb-8 leading-tight">
                  Become a Stock Market Hero!
                </h2>
                <p className="text-xl text-gray-300 mb-10 leading-relaxed max-w-lg">
                  Learn by playing. Virtual trading, gamified learning, AI insights, and real market simulations.
                </p>
                <div className="flex flex-wrap gap-4">
                  <a href="/learning" className="px-8 py-4 bg-gradient-to-r from-emerald-500 to-teal-600 text-lg font-semibold rounded-2xl hover:from-emerald-600 hover:to-teal-700 shadow-2xl transform hover:-translate-y-1 transition-all duration-300">
                    Start Learning
                  </a>
                  <a href="/trading" className="px-8 py-4 border-2 border-white/50 text-lg font-semibold rounded-2xl hover:bg-white hover:text-teal-900 backdrop-blur-sm transition-all duration-300">
                    Start Trading
                  </a>
                </div>
              </div>
              {/* Right Mockup */}
              <div className="lg:w-1/2">
                <div className="relative">
                  <div className="bg-black/20 backdrop-blur-xl rounded-3xl p-8 shadow-2xl border border-white/10">
                    <div className="bg-gradient-to-r from-purple-500/20 to-pink-500/20 rounded-2xl p-6">
                      <div className="flex items-center gap-3 mb-6">
                        <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
                        <span className="text-sm font-medium text-white/80">Live</span>
                      </div>
                      <h3 className="text-2xl font-bold text-white mb-4">Portfolio Value</h3>
                      <div className="text-4xl font-black bg-gradient-to-r from-emerald-400 to-teal-400 bg-clip-text text-transparent mb-2">
                        $25,430
                      </div>
                      <div className="flex items-center gap-2 text-sm text-emerald-400 font-semibold">
                        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                        +2.3%
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>
  
        {/* Features Section */}
        <section className="py-24">
          <div className="container mx-auto px-6">
            <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
              <div className="text-center p-8 bg-white/5 backdrop-blur-xl rounded-3xl border border-white/10 hover:bg-white/10 transition-all duration-300">
                <div className="w-20 h-20 bg-gradient-to-r from-green-400 to-emerald-500 rounded-3xl flex items-center justify-center mx-auto mb-6 shadow-xl">
                  <span className="text-2xl font-bold">💰</span>
                </div>
                <h3 className="text-2xl font-bold text-white mb-4">Money Basics</h3>
                <p className="text-gray-300 leading-relaxed">Master fundamental investing concepts</p>
              </div>
              <div className="text-center p-8 bg-white/5 backdrop-blur-xl rounded-3xl border border-white/10 hover:bg-white/10 transition-all duration-300">
                <div className="w-20 h-20 bg-gradient-to-r from-blue-400 to-cyan-500 rounded-3xl flex items-center justify-center mx-auto mb-6 shadow-xl">
                  <span className="text-2xl font-bold">👥</span>
                </div>
                <h3 className="text-2xl font-bold text-white mb-4">Team Play</h3>
                <p className="text-gray-300 leading-relaxed">Compete with friends and classmates</p>
              </div>
              <div className="text-center p-8 bg-white/5 backdrop-blur-xl rounded-3xl border border-white/10 hover:bg-white/10 transition-all duration-300">
                <div className="w-20 h-20 bg-gradient-to-r from-purple-400 to-pink-500 rounded-3xl flex items-center justify-center mx-auto mb-6 shadow-xl">
                  <span className="text-2xl font-bold">🏆</span>
                </div>
                <h3 className="text-2xl font-bold text-white mb-4">Win Big</h3>
                <p className="text-gray-300 leading-relaxed">Real-world market simulation</p>
              </div>
            </div>
          </div>
        </section>
  
        {/* Performance Cards */}
        <section className="py-16">
          <div className="container mx-auto px-6">
            <div className="grid md:grid-cols-4 gap-6 max-w-4xl mx-auto">
              {[
                { value: "+2.4%", label: "Today", color: "emerald" },
                { value: "-0.8%", label: "Week", color: "red" },
                { value: "+0.9%", label: "Month", color: "emerald" },
                { value: "+5.1%", label: "Year", color: "emerald" }
              ].map((item, idx) => (
                <div key={idx} className="text-center p-6 bg-white/5 backdrop-blur-xl rounded-2xl border border-white/10">
                  <div className={`text-2xl font-black ${item.color === 'emerald' ? 'text-emerald-400' : 'text-red-400'}`}>
                    {item.value}
                  </div>
                  <div className="text-sm text-gray-400 uppercase tracking-wide mt-1">{item.label}</div>
                </div>
              ))}
            </div>
          </div>
        </section>
      </div>
    )
  }
  
  export default HomePage
  