// API Configuration Service
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

class ApiService {
  constructor() {
    this.baseURL = API_BASE_URL
  }

  // Generic request method
  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`
    
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    }

    try {
      const response = await fetch(url, config)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      return await response.json()
    } catch (error) {
      console.error('API request failed:', error)
      throw error
    }
  }

  // GET request
  async get(endpoint) {
    return this.request(endpoint, { method: 'GET' })
  }

  // POST request
  async post(endpoint, data) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data)
    })
  }

  // PUT request
  async put(endpoint, data) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data)
    })
  }

  // DELETE request
  async delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' })
  }

  // Specific API methods
  async getHealth() {
    return this.get('/health')
  }

  async getPublications() {
    return this.get('/api/publications')
  }

  async getTeam() {
    return this.get('/api/team')
  }

  async submitContact(data) {
    return this.post('/api/contact', data)
  }

  // SUMO Simulation API methods
  async getSimulationStatus() {
    return this.get('/api/simulation/status')
  }

  async getDataStatus() {
    return this.get('/api/simulation/data-status')
  }

  async startJourney(start, end) {
    return this.post('/api/simulation/start-journey', { start, end })
  }

  async getVehiclePosition(vehicleId) {
    return this.get(`/api/simulation/vehicle/${vehicleId}/position`)
  }

  async getActiveVehicles() {
    return this.get('/api/simulation/vehicles/active')
  }

  async startSimulation() {
    return this.post('/api/simulation/start')
  }

  async stopSimulation() {
    return this.post('/api/simulation/stop')
  }

  // Trips playback
  async getCurrentTrips() {
    return this.get('/api/trips/current')
  }

  async nextTripsStep() {
    return this.post('/api/trips/next')
  }

  async startTripsPlayback() {
    return this.post('/api/trips/play')
  }

  async stopTripsPlayback() {
    return this.post('/api/trips/stop')
  }

  async getTripsStatus() {
    return this.get('/api/trips/status')
  }


  async completeJourney(vehicleId, actualDuration) {
    return this.post(`/api/simulation/complete-journey?vehicle_id=${vehicleId}&actual_duration=${actualDuration}`)
  }

  async calculateRoute(startX, startY, endX, endY) {
    return this.post(`/api/simulation/calculate-route?start_x=${startX}&start_y=${startY}&end_x=${endX}&end_y=${endY}`)
  }

  async calculateRouteByEdges(startEdge, endEdge) {
    return this.post(`/api/simulation/calculate-route-by-edges?start_edge=${startEdge}&end_edge=${endEdge}`)
  }

  async getSimulationResults(limit = 10) {
    return this.get(`/api/simulation/results?limit=${limit}`)
  }

  async getSimulationStatistics() {
    return this.get('/api/simulation/statistics')
  }

  // Network visualization API methods
  async getNetworkData() {
    return this.get('/api/network/data')
  }
}

// Export a singleton instance
export default new ApiService()
