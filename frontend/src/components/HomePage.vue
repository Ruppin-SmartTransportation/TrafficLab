<template>
  <div>
    <!-- Hero Section -->
    <section id="home" class="bg-gradient-to-r from-blue-600 to-blue-800 text-white py-20">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <h1 class="text-5xl font-bold mb-6">SmartTransportation Lab</h1>
        <p class="text-xl mb-8">Advancing Traffic Simulation and ETA Prediction through AI</p>
        <router-link to="/demo" class="bg-white text-blue-600 px-8 py-3 rounded-lg font-semibold hover:bg-blue-50 transition duration-300 inline-block">
          Try Live Demo
        </router-link>
      </div>
    </section>

    <!-- About Section -->
    <section id="about" class="py-16 bg-gray-50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2 class="text-3xl font-bold text-center mb-12">About Our Lab</h2>
        <div class="grid md:grid-cols-2 gap-8">
          <div>
            <h3 class="text-2xl font-semibold mb-4">Our Mission</h3>
            <p class="text-gray-600 leading-relaxed">
              The SmartTransportation Lab is dedicated to advancing traffic simulation technologies 
              and developing accurate ETA prediction models using cutting-edge machine learning techniques. 
              We combine SUMO traffic simulation with PyTorch-based neural networks to create 
              intelligent transportation solutions.
            </p>
          </div>
          <div>
            <h3 class="text-2xl font-semibold mb-4">Research Focus</h3>
            <ul class="text-gray-600 space-y-2">
              <li>• Traffic flow simulation and modeling</li>
              <li>• Machine learning for ETA prediction</li>
              <li>• Real-time traffic data analysis</li>
              <li>• Intelligent transportation systems</li>
            </ul>
          </div>
        </div>
      </div>
    </section>

    <!-- Team Section -->
    <section id="team" class="py-16">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2 class="text-3xl font-bold text-center mb-12">Our Team</h2>
        <div class="grid md:grid-cols-3 gap-8">
          <div class="text-center">
            <div class="w-32 h-32 bg-gray-300 rounded-full mx-auto mb-4"></div>
            <h3 class="text-xl font-semibold">Dr. [Your Name]</h3>
            <p class="text-blue-600">Principal Investigator</p>
            <p class="text-gray-600 mt-2">Traffic Simulation & Machine Learning</p>
          </div>
          <div class="text-center">
            <div class="w-32 h-32 bg-gray-300 rounded-full mx-auto mb-4"></div>
            <h3 class="text-xl font-semibold">[Researcher Name]</h3>
            <p class="text-blue-600">Research Scientist</p>
            <p class="text-gray-600 mt-2">Data Analysis & Visualization</p>
          </div>
          <div class="text-center">
            <div class="w-32 h-32 bg-gray-300 rounded-full mx-auto mb-4"></div>
            <h3 class="text-xl font-semibold">[Student Name]</h3>
            <p class="text-blue-600">PhD Student</p>
            <p class="text-gray-600 mt-2">SUMO Integration & ETA Models</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Research Section -->
    <section id="research" class="py-16">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2 class="text-3xl font-bold text-center mb-12">Our Research</h2>
        <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          <div class="bg-white rounded-lg shadow-md p-6">
            <div class="text-4xl mb-4">🚗</div>
            <h3 class="text-xl font-semibold mb-3">Traffic Simulation</h3>
            <p class="text-gray-600 mb-4">
              Advanced SUMO-based traffic simulation for modeling complex urban traffic scenarios 
              and understanding traffic flow dynamics.
            </p>
            <ul class="text-sm text-gray-500 space-y-1">
              <li>• Real-time traffic modeling</li>
              <li>• Multi-modal transportation</li>
              <li>• Intersection optimization</li>
            </ul>
          </div>
          
          <div class="bg-white rounded-lg shadow-md p-6">
            <div class="text-4xl mb-4">🤖</div>
            <h3 class="text-xl font-semibold mb-3">Machine Learning</h3>
            <p class="text-gray-600 mb-4">
              Deep learning models for accurate ETA prediction using PyTorch, 
              processing real-time traffic data and historical patterns.
            </p>
            <ul class="text-sm text-gray-500 space-y-1">
              <li>• Neural network architectures</li>
              <li>• Time series prediction</li>
              <li>• Data preprocessing pipelines</li>
            </ul>
          </div>
          
          <div class="bg-white rounded-lg shadow-md p-6">
            <div class="text-4xl mb-4">📊</div>
            <h3 class="text-xl font-semibold mb-3">Data Analytics</h3>
            <p class="text-gray-600 mb-4">
              Comprehensive analysis of traffic patterns, performance metrics, 
              and predictive modeling for intelligent transportation systems.
            </p>
            <ul class="text-sm text-gray-500 space-y-1">
              <li>• Statistical analysis</li>
              <li>• Performance evaluation</li>
              <li>• Visualization tools</li>
            </ul>
          </div>
        </div>
        
        <!-- Research Methodology -->
        <div class="mt-16 bg-gray-50 rounded-lg p-8">
          <h3 class="text-2xl font-semibold mb-6 text-center">Research Methodology</h3>
          <div class="grid md:grid-cols-2 gap-8">
            <div>
              <h4 class="text-lg font-semibold mb-3">Data Collection</h4>
              <p class="text-gray-600 mb-4">
                We collect real-time traffic data from multiple sources including sensors, 
                GPS traces, and simulation outputs to build comprehensive datasets.
              </p>
            </div>
            <div>
              <h4 class="text-lg font-semibold mb-3">Model Development</h4>
              <p class="text-gray-600 mb-4">
                Our models combine traditional traffic engineering principles with 
                modern machine learning techniques for robust ETA predictions.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Live Demo Section -->
    <section id="demo" class="py-16 bg-blue-50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <h2 class="text-3xl font-bold mb-8">Live Demo</h2>
        <div class="bg-white rounded-lg shadow-lg p-8 max-w-2xl mx-auto">
          <h3 class="text-2xl font-semibold mb-4">SUMO-ETA Model Simulation</h3>
          <p class="text-gray-600 mb-6">
            Experience our real-time traffic simulation combined with AI-powered ETA prediction. 
            Watch as our system processes live traffic data and provides accurate arrival time estimates.
          </p>
          <router-link to="/demo" class="bg-blue-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-blue-700 transition duration-300 inline-block">
            Launch Interactive Demo
          </router-link>
        </div>
      </div>
    </section>

    <!-- Publications Section -->
    <section id="publications" class="py-16">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2 class="text-3xl font-bold text-center mb-12">Recent Publications</h2>
        <div class="space-y-6">
          <div class="bg-white shadow-md rounded-lg p-6">
            <h3 class="text-xl font-semibold mb-2">Advanced ETA Prediction Using Deep Learning in Traffic Simulation</h3>
            <p class="text-gray-600 mb-2">Journal of Transportation Research, 2024</p>
            <p class="text-sm text-gray-500">Authors: [Your Name], [Co-author], [Co-author]</p>
          </div>
          <div class="bg-white shadow-md rounded-lg p-6">
            <h3 class="text-xl font-semibold mb-2">SUMO Integration for Real-time Traffic Data Processing</h3>
            <p class="text-gray-600 mb-2">International Conference on Intelligent Transportation Systems, 2023</p>
            <p class="text-sm text-gray-500">Authors: [Your Name], [Co-author]</p>
          </div>
          <div class="bg-white shadow-md rounded-lg p-6">
            <h3 class="text-xl font-semibold mb-2">Machine Learning Approaches for Traffic Flow Prediction</h3>
            <p class="text-gray-600 mb-2">Transportation Research Part C, 2023</p>
            <p class="text-sm text-gray-500">Authors: [Your Name], [Co-author], [Co-author]</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Contact Section -->
    <section id="contact" class="py-16 bg-gray-900 text-white">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <h2 class="text-3xl font-bold mb-8">Contact Us</h2>
        <div class="grid md:grid-cols-3 gap-8">
          <div>
            <h3 class="text-xl font-semibold mb-2">Email</h3>
            <p class="text-gray-300">contact@smarttransportationlab.com</p>
          </div>
          <div>
            <h3 class="text-xl font-semibold mb-2">Location</h3>
            <p class="text-gray-300">[Your University/Institution]</p>
          </div>
          <div>
            <h3 class="text-xl font-semibold mb-2">Phone</h3>
            <p class="text-gray-300">+1 (555) 123-4567</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Footer -->
    <footer class="bg-gray-800 text-white py-8">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <p>&copy; 2024 SmartTransportation Lab. All rights reserved.</p>
        <p class="text-sm text-gray-400 mt-2">
          API Status: 
          <span :class="apiStatus === 'healthy' ? 'text-green-400' : 'text-red-400'">
            {{ apiStatus }}
          </span>
        </p>
      </div>
    </footer>
  </div>
</template>

<script>
import apiService from '../services/api.js'

export default {
  name: 'HomePage',
  data() {
    return {
      apiStatus: 'checking...'
    }
  },
  async mounted() {
    // Check API health
    try {
      const health = await apiService.getHealth()
      this.apiStatus = health.status
    } catch (error) {
      this.apiStatus = 'offline'
      console.error('API health check failed:', error)
    }
  }
}
</script>
