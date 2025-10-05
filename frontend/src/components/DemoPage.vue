<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Demo Header -->
    <div class="bg-gradient-to-r from-blue-600 to-blue-800 text-white py-5">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center">
          <router-link to="/" class="text-2xl font-bold hover:text-blue-200">
            SmartTransportation Lab
          </router-link>
          <h1 class="text-xl">ETA Prediction Performance Testing</h1>
        </div>
      </div>
    </div>

    <!-- Main Demo Content -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <div class="flex gap-6">
              
              <!-- Network Map (Full width) -->
              <div class="w-full bg-white rounded-lg shadow-lg">
          <!-- Simulation Map -->
          <div class="relative h-full">
            <div class="bg-gray-100 rounded-t-lg p-4 border-b">
              <div class="flex items-center justify-between">
                <div>
                  <h2 class="text-xl font-semibold">Traffic Network Map</h2>
                  <div class="text-sm text-gray-600 mt-1">
                    Click on roads to set start and destination points
                  </div>
                </div>
                
                <!-- Control Buttons -->
                <div class="flex space-x-3">
              <!-- Simulation Playback Controls - Always show -->
              <div class="flex items-center space-x-2">
                <!-- Reset Points Button - Show when points are selected but journey not running -->
                    <button 
                  v-if="startPoint && !isJourneyRunning"
                  @click="resetPoints"
                  class="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg font-semibold transition duration-300 text-sm"
                    >
                  🔄 Reset Points
                    </button>
                
                    <button 
                  @click="handleMainButtonClick()"
                  :class="getMainButtonClass()"
                  class="text-white px-4 py-2 rounded-lg font-semibold transition duration-300 text-sm"
                    >
                  {{ getMainButtonText() }}
                    </button>
                <div class="text-sm text-gray-600">
                  Trips: {{ simulationStatus.trips_added || 0 }}
                  </div>
                <div class="text-sm text-gray-600">
                  Active: {{ simulationStatus.vehicles_in_route || 0 }}
                </div>
                <div class="text-sm text-gray-600 font-mono">
                  Time: {{ simulationTime }}
                </div>
              </div>
                </div>
              </div>
            </div>
            
            <!-- SUMO Network Container -->
                  <div 
                    class="relative bg-gray-300 h-[calc(92vh-276px)]"
                    ref="mapContainer"
                  >
              <!-- SUMO Network Visualization -->
              <svg 
                ref="networkSvg"
                :viewBox="svgViewBox" 
                width="100%" 
                height="100%" 
                class="absolute inset-0 cursor-crosshair map-container" 
                style="background: #f1f5f9; min-height: 690px;"
                preserveAspectRatio="xMidYMid meet"
                        @mousemove="handleMouseMove"
                @click="handleMapClick"
              >
                <!-- SUMO Network Edges (Roads) -->
                <g v-if="networkData && networkData.edges">
                  <template v-for="edge in networkData.edges" :key="edge.id">
                    <!-- Use path for express edges with detailed shape, line for regular roads -->
                        <path 
                      v-if="isExpressEdge(edge) && edge.shape_points && edge.shape_points.length > 0"
                      :d="getPathData(edge.shape_points)"
                          :stroke="getRouteStrokeColor(edge)"
                          :stroke-width="getRouteStrokeWidth(edge)"
                          :opacity="getRoadOpacity(edge)"
                          :class="getRoadClass(edge)"
                      :data-road-name="edge.id"
                          fill="none"
                      @click="handleEdgeClick(edge, $event)"
                    />
                    <!-- Simple line representation for regular roads -->
                    <line 
                      v-else
                      :x1="getJunctionPosition(edge.from_junction)?.x || 0"
                      :y1="getJunctionPosition(edge.from_junction)?.y || 0"
                      :x2="getJunctionPosition(edge.to_junction)?.x || 0"
                      :y2="getJunctionPosition(edge.to_junction)?.y || 0"
                      :stroke="getRouteStrokeColor(edge)"
                      :stroke-width="getRouteStrokeWidth(edge)"
                      :opacity="getRoadOpacity(edge)"
                          :class="getRoadClass(edge)"
                      :data-road-name="edge.id"
                      @click="handleEdgeClick(edge, $event)"
                        />
                  </template>
                </g>
                
                <!-- SUMO Network Junctions -->
                <g v-if="networkData && networkData.junctions">
                  <circle 
                    v-for="junction in networkData.junctions" 
                    :key="junction.id"
                    :cx="junction.x" 
                    :cy="junction.y" 
                    r="1.5" 
                    fill="#1f2937"
                    opacity="0.6"
                  />
                </g>
                
                
                <!-- Start point marker -->
                <circle 
                  v-if="startPoint" 
                  :cx="startPoint.x" 
                  :cy="startPoint.y" 
                  r="100" 
                  fill="#10b981" 
                  stroke="white" 
                  stroke-width="8"
                  class="cursor-pointer drop-shadow-lg"
                />
                <text 
                  v-if="startPoint" 
                  :x="startPoint.x" 
                  :y="startPoint.y + 60" 
                  text-anchor="middle" 
                  fill="black" 
                  font-size="180" 
                  font-weight="bold"
                >
                  S
                </text>
                
                
                <!-- Destination point marker -->
                <circle 
                  v-if="destinationPoint" 
                  :cx="destinationPoint.x" 
                  :cy="destinationPoint.y" 
                  r="100" 
                  fill="#ef4444" 
                  stroke="white" 
                  stroke-width="8"
                  class="cursor-pointer drop-shadow-lg"
                />
                <text 
                  v-if="destinationPoint" 
                  :x="destinationPoint.x" 
                  :y="destinationPoint.y + 60" 
                  text-anchor="middle" 
                  fill="black" 
                  font-size="180" 
                  font-weight="bold"
                >
                  D
                </text>
                
                
                <!-- Route path -->
                <path 
                  v-if="routePath" 
                  :d="routePath" 
                  stroke="#3b82f6" 
                  stroke-width="6" 
                  fill="none" 
                  stroke-dasharray="10,5"
                  opacity="0.8"
                />
                
                <!-- Real Vehicles from Simulation -->
                <g v-if="activeVehicles && activeVehicles.length > 0">
                <circle 
                    v-for="vehicle in activeVehicles.filter(v => !isNaN(v.x) && !isNaN(v.y))"
                    :key="vehicle.id"
                    :cx="vehicle.x"
                    :cy="vehicle.y"
                    r="36"
                    :fill="getVehicleColor(vehicle.type, vehicle.status)"
                    :stroke="getVehicleStroke(vehicle.type, vehicle.status)"
                  stroke-width="6"
                    class="vehicle-marker"
                    opacity="0.8"
                />
                </g>
                
              </svg>


              <!-- Instruction Overlay - Only show when simulation is stopped -->
              <div v-if="!isSimulationPlaying" class="absolute top-4 left-4 pointer-events-none">
                <div class="bg-white bg-opacity-95 rounded-xl shadow-xl p-4 text-center max-w-xs animate-pulse">
                  <div class="text-2xl mb-2 animate-bounce">
                    <span v-if="!startPoint">📍</span>
                    <span v-else-if="!destinationPoint">🎯</span>
                    <span v-else>🚀</span>
                  </div>
                  <h3 class="text-lg font-bold text-gray-800 mb-1">
                    <span v-if="!startPoint">Set Starting Point</span>
                    <span v-else-if="!destinationPoint">Set Destination</span>
                    <span v-else>Ready to Start!</span>
                  </h3>
                  <p class="text-sm text-gray-600">
                    {{ getInstructionText() }}
                  </p>
                </div>
              </div>
              
              <!-- Invalid Click Message -->
              <div v-if="invalidClickMessage" class="absolute top-4 right-4 pointer-events-none">
                <div class="bg-red-500 text-white px-4 py-2 rounded-lg shadow-lg animate-pulse">
                  <div class="flex items-center">
                    <span class="text-lg mr-2">⚠️</span>
                    <span class="text-sm font-medium">{{ invalidClickMessage }}</span>
                  </div>
                </div>
              </div>
              
              <!-- Simulation Running Overlay - Small top right -->
              <div v-if="showSimulationOverlay" class="absolute top-4 right-4 pointer-events-auto">
                <div class="bg-orange-500 text-white px-4 py-2 rounded-lg shadow-lg animate-pulse">
                  <div class="flex items-center">
                    <span class="text-lg mr-2">🚗</span>
                    <span class="text-sm font-medium">Stop simulation to add trip</span>
                    <button 
                      @click="closeSimulationOverlay"
                      class="ml-2 text-white hover:text-gray-200"
                    >
                      ✕
                    </button>
                </div>
              </div>
            </div>

              
        <!-- Loading indicator -->
        <div v-if="!networkData" class="absolute inset-0 flex items-center justify-center bg-white bg-opacity-75">
          <div class="text-center">
            <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p class="text-lg text-gray-600">Loading SUMO network...</p>
                </div>
              </div>
            </div>
            
        </div>
      </div>

          </div>
    </div>
  </div>
</template>

<script>
import apiService from '../services/api.js'

export default {
  name: 'DemoPage',
  components: {
  },
  data() {
    return {
      
      // Mouse position for proximity detection
      mousePosition: { x: 0, y: 0 },
      
      
      // Road switching debounce timer
      roadSwitchTimer: null,
      
      
      // Point placement
      startPoint: null,
      destinationPoint: null,
      
      // Journey state
      isJourneyRunning: false,
      
      // Simulation overlay
      showSimulationOverlay: false,
      
      // Route data
      calculatedRoute: null,
      
      // Invalid click feedback
      invalidClickMessage: '',
      
      // Animation
      animationInterval: null,

              // Network visualization
              networkData: null,
              networkBounds: null,
      svgViewBox: "0 0 1000 1000", // Default viewBox, will be calculated from network data
      
      // Simulation playback
      isSimulationPlaying: false,
      simulationStatus: {
        vehicles: 0,
        vehicles_in_route: 0,
        current_step: 0
      },
      
      // Vehicle management
      activeVehicles: [],
      vehicleUpdateInterval: null,
      
      // Simulation status
      simulationTime: '00:00:00:00',
      
      // Route data
      routePath: null,
      
      // Animation intervals
      simulationUpdateInterval: null
    }
  },
  
  methods: {

    async loadNetworkData() {
      console.log('🔄 Starting to load network data...')
      try {
        console.log('📡 Making API call to getNetworkData...')
        const response = await apiService.getNetworkData()
        console.log('✅ API response received:', response)
        this.networkData = response
        this.networkBounds = response.bounds
        
        console.log('📊 Network data assigned:', {
          hasNetworkData: !!this.networkData,
          hasEdges: !!this.networkData?.edges,
          edgesCount: this.networkData?.edges?.length || 0,
          hasJunctions: !!this.networkData?.junctions,
          junctionsCount: this.networkData?.junctions?.length || 0,
          hasBounds: !!this.networkBounds
        })
        
                // Calculate optimal viewBox with asymmetric padding
                // Network bounds: x: 0 to 18000, y: -6264.96 to 5000
                // Network width: 18000, height: 11264.96
                const paddingX = 0.02 // 2% padding on sides (restored)
                const paddingY = 0.01 // 1% padding on top and bottom (minimal)
                const width = this.networkBounds.max_x - this.networkBounds.min_x
                const height = this.networkBounds.max_y - this.networkBounds.min_y
                const paddingXValue = width * paddingX
                const paddingYValue = height * paddingY
                
                this.svgViewBox = `${this.networkBounds.min_x - paddingXValue} ${this.networkBounds.min_y - paddingYValue} ${width + 2 * paddingXValue} ${height + 2 * paddingYValue}`
        console.log('Using calculated viewBox:', this.svgViewBox)
        console.log('Padding values:', { paddingX, paddingY, paddingXValue, paddingYValue })
        
        // Force reactive update
        this.$nextTick(() => {
          console.log('ViewBox updated:', this.svgViewBox)
        })
        console.log('Network data loaded:', {
          edges: this.networkData?.edges?.length || 0,
          junctions: this.networkData?.junctions?.length || 0,
          bounds: this.networkBounds,
          calculatedViewBox: {
            x: this.networkBounds.min_x - paddingXValue,
            y: this.networkBounds.min_y - paddingYValue,
            width: width + 2 * paddingXValue,
            height: height + 2 * paddingYValue
          }
        })
      } catch (error) {
        console.error('❌ Error loading network data:', error)
        this.networkData = null
      }
    },

    // Convert screen coordinates to network coordinates
    screenToNetwork(screenX, screenY) {
      // Validate input coordinates
      if (isNaN(screenX) || isNaN(screenY)) {
        console.warn('Invalid coordinates:', screenX, screenY)
        return { x: 0, y: 0 }
      }
      
      if (!this.networkBounds) {
        console.warn('No network bounds available')
        return { x: screenX, y: screenY }
      }
      
      const svgRect = this.$refs.networkSvg?.getBoundingClientRect()
      if (!svgRect) {
        console.warn('No SVG element found')
        return { x: screenX, y: screenY }
      }
      
      const scaleX = (this.networkBounds.max_x - this.networkBounds.min_x) / svgRect.width
      const scaleY = (this.networkBounds.max_y - this.networkBounds.min_y) / svgRect.height
      
      // screenX and screenY are already relative to the SVG element
      let networkX = this.networkBounds.min_x + screenX * scaleX
      let networkY = this.networkBounds.min_y + screenY * scaleY
      
      // Validate output coordinates
      if (isNaN(networkX) || isNaN(networkY)) {
        console.warn('Invalid network coordinates:', networkX, networkY, 'from', screenX, screenY)
        return { x: 0, y: 0 }
      }
      
      return { x: networkX, y: networkY }
    },

    // Convert network coordinates to screen coordinates
    networkToScreen(networkX, networkY) {
      if (!this.networkBounds) return { x: networkX, y: networkY }
      
      const svgRect = this.$refs.networkSvg?.getBoundingClientRect()
      if (!svgRect) return { x: networkX, y: networkY }
      
      const scaleX = svgRect.width / (this.networkBounds.max_x - this.networkBounds.min_x)
      const scaleY = svgRect.height / (this.networkBounds.max_y - this.networkBounds.min_y)
      
      return {
        x: (networkX - this.networkBounds.min_x) * scaleX,
        y: (networkY - this.networkBounds.min_y) * scaleY
      }
    },

    // Get junction position by ID
    getJunctionPosition(junctionId) {
      if (!this.networkData?.junctions) return null
      return this.networkData.junctions.find(j => j.id === junctionId)
    },
    
    isExpressEdge(edge) {
      // Check if an edge is an express edge based on naming patterns
      if (!edge || !edge.id) return false
      
      // Express edges are the main connecting roads between zones
      if (edge.id.startsWith('-E') || edge.id.startsWith('E')) {
        return true
      }
      
      const expressPatterns = [
        'BI', 'BH', 'BG', 'BF', 'BE', 'BD', 'BC', 'BA', 'BB',
        'AQ', 'AP', 'AO', 'AN', 'AM', 'AL', 'AK', 'AJ', 'AI', 'AH', 'AG', 'AF', 'AE', 'AD', 'AC', 'AB', 'AA'
      ]
      
      for (const pattern of expressPatterns) {
        if (edge.id.startsWith(pattern) && edge.id.length > 3) {
          return true
        }
      }
      return false
    },
    
    getPathData(shapePoints) {
      if (!shapePoints || shapePoints.length < 2) return ''
      
      // Create SVG path from shape points
      let pathData = `M ${shapePoints[0][0]} ${shapePoints[0][1]}`
      
      for (let i = 1; i < shapePoints.length; i++) {
        pathData += ` L ${shapePoints[i][0]} ${shapePoints[i][1]}`
      }
      
      return pathData
    },
    
          // Vehicle color based on type and status
          getVehicleColor(vehicleType, status) {
            // White if stagnant
            if (status === 'stagnant') {
              return '#ffffff'
            }

            // Color based on vehicle type
            switch(vehicleType) {
              case 'passenger':
                return '#3b82f6'  // Blue
              case 'bus':
                return '#f59e0b'  // Orange
              case 'truck':
                return '#10b981'  // Green
              default:
                return '#6b7280'  // Gray
            }
          },
    
          // Vehicle stroke color
          getVehicleStroke(vehicleType, status) {
            // White stroke for stagnant vehicles
            if (status === 'stagnant') {
              return '#ffffff'
            }

            // Darker stroke for better visibility
            switch(vehicleType) {
              case 'passenger':
                return '#1d4ed8'  // Dark blue
              case 'bus':
                return '#d97706'  // Dark orange
              case 'truck':
                return '#059669'  // Dark green
              default:
                return '#374151'  // Dark gray
      }
    },

    // Convert lane shape coordinates to SVG path
    getLanePath(shape) {
      if (!shape || shape.length < 2) return ''
      
      // SUMO and SVG both use positive Y downward, so no flip needed
      let path = `M ${shape[0].x} ${shape[0].y}`
      for (let i = 1; i < shape.length; i++) {
        path += ` L ${shape[i].x} ${shape[i].y}`
      }
      return path
    },
    
    // Find the closest point on a line segment
    getClosestPointOnLine(px, py, x1, y1, x2, y2) {
      const A = px - x1
      const B = py - y1
      const C = x2 - x1
      const D = y2 - y1
      
      const dot = A * C + B * D
      const lenSq = C * C + D * D
      
      if (lenSq === 0) return { x: x1, y: y1 }
      
      let param = dot / lenSq
      
      // Clamp to line segment
      param = Math.max(0, Math.min(1, param))
      
      return {
        x: x1 + param * C,
        y: y1 + param * D
      }
    },
    
    // Find the closest point on a specific road
    findClosestPointOnRoad(clickX, clickY, road) {
      if (!road || !road.lanes) return null
      
      let closestPoint = null
      let minDistance = Infinity
      
      for (const lane of road.lanes) {
        if (!lane.shape || lane.shape.length < 2) continue
        
        // Check each segment of the lane
        for (let i = 0; i < lane.shape.length - 1; i++) {
          const point1 = lane.shape[i]
          const point2 = lane.shape[i + 1]
          
          // Find the closest point on this line segment
          const segmentPoint = this.getClosestPointOnLine(
            clickX, clickY,
            point1.x, point1.y,
            point2.x, point2.y
          )
          
          const distance = Math.sqrt(
            Math.pow(clickX - segmentPoint.x, 2) + 
            Math.pow(clickY - segmentPoint.y, 2)
          )
          
          if (distance < minDistance) {
            minDistance = distance
            closestPoint = {
              x: segmentPoint.x,
              y: segmentPoint.y,
              road: road,
              lane: lane
            }
          }
        }
      }
      
      return closestPoint
    },
    
    getInstructionText() {
      if (!this.startPoint) {
        return "Click on a road to set your starting location"
      } else if (!this.destinationPoint) {
        return "Click on a road to set your destination"
      } else if (!this.isSimulationRunning) {
        return "Click 'Start Journey' to begin the simulation"
      } else {
        return "Vehicle is traveling to destination..."
      }
    },
    
    resetPoints() {
      // Reset both starting and destination points
      this.startPoint = null
      this.destinationPoint = null
      this.routePath = null
      this.isJourneyRunning = false
      console.log('🔄 Points reset - ready to select new starting point')
    },
    
    
    getMainButtonText() {
      if (this.isSimulationPlaying) {
        return '⏹️ Stop Simulation'
      } else if (this.isJourneyRunning) {
        return '⏹️ Stop Simulation'
      } else if (this.startPoint && this.destinationPoint) {
        return '🚀 Start Journey'
      } else {
        return '▶️ Play Simulation'
      }
    },
    
    getMainButtonClass() {
      if (this.isSimulationPlaying) {
        return 'bg-red-600 hover:bg-red-700'
      } else if (this.isJourneyRunning) {
        return 'bg-red-600 hover:bg-red-700'
      } else if (this.startPoint && this.destinationPoint) {
        return 'bg-green-600 hover:bg-green-700'
      } else {
        return 'bg-blue-600 hover:bg-blue-700'
      }
    },
    
    handleMainButtonClick() {
      if (this.isSimulationPlaying) {
        this.stopSimulationPlayback()
        // Reset points when stopping main simulation
        this.startPoint = null
        this.destinationPoint = null
        this.routePath = null
        this.isJourneyRunning = false
        console.log('🔄 Points reset after stopping main simulation')
      } else if (this.isJourneyRunning) {
        this.stopJourney()
      } else if (this.startPoint && this.destinationPoint) {
        this.startJourney()
      } else {
        this.startSimulationPlayback()
      }
    },
    
    startJourney() {
      if (!this.startPoint || !this.destinationPoint) return
      
      console.log('🚀 Starting journey from', this.startPoint, 'to', this.destinationPoint)
      
      // Start simulation with additional vehicle
      this.startSimulationPlayback()
      this.isJourneyRunning = true
      
      // TODO: Add vehicle to simulation with route from startPoint to destinationPoint
      console.log('🚗 Vehicle added to simulation with route')
    },
    
    stopJourney() {
      console.log('⏹️ Stopping journey')
      
      // Stop the simulation
      this.stopSimulationPlayback()
      this.isJourneyRunning = false
      
      // Reset the points
      this.startPoint = null
      this.destinationPoint = null
      this.routePath = null
      
      // TODO: Remove vehicle from simulation
      console.log('🚗 Vehicle removed from simulation')
      console.log('🔄 Points reset after journey stop')
    },
    
    handleMapClick(event) {
      // Only show overlay if simulation is running and clicking on empty SVG area
      if ((this.isSimulationPlaying || this.isJourneyRunning) && event.target.tagName === 'svg') {
        this.showSimulationOverlay = true
        console.log('🚗 Simulation running - showing overlay on map click')
      }
    },
    
    closeSimulationOverlay() {
      this.showSimulationOverlay = false
      console.log('✅ Simulation overlay closed')
    },
    
    handleEdgeClick(edge, event) {
      // Only allow clicking when simulation is stopped
      if (this.isSimulationPlaying || this.isJourneyRunning) {
        event.stopPropagation()
        this.showSimulationOverlay = true
        return
      }
      
      console.log('🛣️ Edge clicked:', edge.id)
      
      // Calculate the exact middle position of the edge
      let x, y
      
      if (edge.shape_points && edge.shape_points.length > 0) {
        // For express edges with shape points, calculate the exact middle point
        const totalLength = edge.shape_points.length
        const midIndex = Math.floor(totalLength / 2)
        
        // If we have an even number of points, interpolate between the two middle points
        if (totalLength % 2 === 0 && midIndex > 0) {
          const point1 = edge.shape_points[midIndex - 1]
          const point2 = edge.shape_points[midIndex]
          x = (point1[0] + point2[0]) / 2
          y = (point1[1] + point2[1]) / 2
        } else {
          // Use the exact middle point
          x = edge.shape_points[midIndex][0]
          y = edge.shape_points[midIndex][1]
        }
      } else {
        // For regular edges, use the exact midpoint between junctions
        const fromJunction = this.getJunctionPosition(edge.from_junction)
        const toJunction = this.getJunctionPosition(edge.to_junction)
        if (fromJunction && toJunction) {
          x = (fromJunction.x + toJunction.x) / 2
          y = (fromJunction.y + toJunction.y) / 2
        } else {
          // Fallback to center of view
          x = 0
          y = 0
        }
      }
      
      if (!this.startPoint) {
        // Set starting point
        this.startPoint = { id: edge.id, x: x, y: y }
        this.isJourneyRunning = false // Reset journey state when new starting point is set
        console.log('📍 Starting point set:', this.startPoint)
      } else if (!this.destinationPoint) {
        // Set destination point
        this.destinationPoint = { id: edge.id, x: x, y: y }
        this.isJourneyRunning = false // Reset journey state when new destination point is set
        console.log('🎯 Destination point set:', this.destinationPoint)
      }
      // If both points are already set, do nothing (user should use reset button)
    },
    
    getRoadClass(edge) {
      let baseClass = "road-path"
      
      // Check if it's an expressway (any pattern starting with E)
      if (edge.id && (edge.id.startsWith('-E') || edge.id.startsWith('E'))) {
        baseClass += " expressway"
      }
      
      // Add clickable class when simulation is stopped
      if (!this.isSimulationPlaying) {
        baseClass += " clickable"
      }
      
      return baseClass
    },
    
    getRoadStrokeColor(edge) {
      // Expressways are blue, regular roads are dark gray for better visibility
      if (edge.id && (edge.id.startsWith('-E') || edge.id.startsWith('E'))) {
        return "#1e40af"  // Darker blue for expressways
      }
      return "#374151"  // Dark gray for regular roads - more visible than black
    },
    
    getRoadStrokeWidth(edge) {
      // All roads have thick strokes
      if (edge.id && (edge.id.startsWith('-E') || edge.id.startsWith('E'))) {
        return "17"  // Expressways
      }
      return "15"  // Regular roads
    },
    
    getRoadOpacity(edge) {
      // Expressways are dimmed, regular roads are full opacity
      if (edge.id && (edge.id.startsWith('-E') || edge.id.startsWith('E'))) {
        return "0.6"
      }
      return "1.0"
    },
    
    isExpressway(edge) {
      return edge.id && (edge.id.startsWith('-E') || edge.id.startsWith('E'))
    },
    
    isRouteEdge(edge) {
      // Check if this edge is part of the calculated route
      if (!this.calculatedRoute || !this.calculatedRoute.route_edges) return false
      const isRoute = this.calculatedRoute.route_edges.includes(edge.id)
      if (isRoute) {
        console.log(`🟠 Route edge found: ${edge.id}`)
      }
      return isRoute
    },
    
    getRouteStrokeColor(edge) {
      // Return bright fluorescent orange for route edges
      if (this.isRouteEdge(edge)) {
        return "#ff4500"
      }
      
      // Expressways are blue, regular roads are dark gray for better visibility
      if (this.isExpressway(edge)) {
        return "#1e40af"  // Darker blue for expressways
      }
      return "#374151"  // Dark gray for regular roads - more visible than black
    },
    
    getRouteStrokeWidth(edge) {
      // Make route edges much thicker and more visible
      if (this.isRouteEdge(edge)) {
        return "30"
      }
      
      return this.getRoadStrokeWidth(edge)
    },
    
    
    showInvalidClickFeedback() {
      // Show a temporary message that the click was not on a road
      this.invalidClickMessage = "Please click on a road, not empty space"
      setTimeout(() => {
        this.invalidClickMessage = ""
      }, 2000)
    },
    
    showExpresswayNotAllowedFeedback() {
      // Show a temporary message that expressways are not allowed
      this.invalidClickMessage = "Expressways are not allowed for point placement. Please choose a regular road."
      setTimeout(() => {
        this.invalidClickMessage = ""
      }, 3000)
    },
    
    
    handleMouseMove(event) {
      // Track mouse position for proximity detection
      const svg = this.$refs.networkSvg
      if (!svg) return

      const rect = svg.getBoundingClientRect()
      this.mousePosition = {
        x: event.clientX - rect.left,
        y: event.clientY - rect.top
      }
      
    },
    
    
    
    async calculateRoute() {
      if (!this.startPoint || !this.destinationPoint) return
      
      try {
        console.log('🛣️ Calculating route...', {
          startEdge: this.startPoint.road.id,
          endEdge: this.destinationPoint.road.id
        })
        
        const routeData = await apiService.calculateRouteByEdges(
          this.startPoint.road.id,
          this.destinationPoint.road.id
        )
        
        if (routeData.success) {
          this.calculatedRoute = routeData
          console.log('✅ Route calculated:', routeData)
          console.log('🟠 Route edges:', routeData.route_edges)
          console.log('🟠 Calculated route set:', this.calculatedRoute)
        } else {
          console.error('❌ Route calculation failed:', routeData.error)
        }
      } catch (error) {
        console.error('❌ Error calculating route:', error)
      }
    },
    
    async startSimulation() {
      if (!this.startPoint || !this.destinationPoint) return
      
      try {
        // Call the real API to start journey
        const response = await apiService.startJourney(
          { x: this.startPoint.x, y: this.startPoint.y },
          { x: this.destinationPoint.x, y: this.destinationPoint.y }
        )
        
        this.predictedETA = response.predicted_eta
        this.currentPrediction = this.predictedETA
        this.currentVehicleId = response.vehicle_id
        
        // Create route path (simplified straight line for demo)
        const startX = this.startPoint.x
        const startY = this.startPoint.y
        const endX = this.destinationPoint.x
        const endY = this.destinationPoint.y
        
        this.routePath = `M ${startX} ${startY} L ${endX} ${endY}`
      } catch (error) {
        console.error('Error starting journey:', error)
        // Fallback to simulated data
        this.predictedETA = Math.floor(Math.random() * 20) + 5
        this.currentPrediction = this.predictedETA
        this.currentVehicleId = `vehicle_${Date.now()}`
        
        const startX = this.startPoint.x
        const startY = this.startPoint.y
        const endX = this.destinationPoint.x
        const endY = this.destinationPoint.y
        
        this.routePath = `M ${startX} ${startY} L ${endX} ${endY}`
      }
    },
    
    startSimulation() {
      if (!this.startPoint) return
      
      // Reset the source point as requested
      this.startPoint = null
      this.destinationPoint = null
      this.routePath = null
      this.isJourneyRunning = false
      
      // Start the simulation
      this.startSimulationPlayback()
      console.log('▶️ Simulation started - source point reset')
    },
    
    animateVehicle() {
      const startX = this.startPoint.x
      const startY = this.startPoint.y
      const endX = this.destinationPoint.x
      const endY = this.destinationPoint.y
      
      const totalDistance = Math.sqrt(Math.pow(endX - startX, 2) + Math.pow(endY - startY, 2))
      const duration = this.predictedETA * 1000 // Convert to milliseconds
      const steps = 60 // 60 steps for smooth animation
      const stepDuration = duration / steps
      
      let currentStep = 0
      
      this.animationInterval = setInterval(() => {
        currentStep++
        const progress = currentStep / steps
        
        if (progress >= 1) {
          // Journey complete
          this.completeJourney()
          return
        }
        
        // Update vehicle position
        this.vehiclePosition = {
          x: startX + (endX - startX) * progress,
          y: startY + (endY - startY) * progress
        }
      }, stepDuration)
    },
    
    async completeJourney() {
      this.isSimulationRunning = false
      this.actualDuration = Math.floor((Date.now() - this.simulationStartTime) / 1000 / 60) // Convert to minutes
      
      try {
        // Call the real API to complete journey
        if (this.currentVehicleId) {
          await apiService.completeJourney(this.currentVehicleId, this.actualDuration * 60) // Convert to seconds
        }
        
        // Load updated results and statistics
        await this.loadResults()
        await this.loadStatistics()
        
      } catch (error) {
        console.error('Error completing journey:', error)
        // Fallback to local calculation
        this.calculateLocalResult()
      }
      
      // Show journey summary instead of immediately resetting
      this.showJourneySummary = true
      
      if (this.animationInterval) {
        clearInterval(this.animationInterval)
        this.animationInterval = null
      }
    },
    
    calculateLocalResult() {
      // Calculate accuracy
      const error = Math.abs(this.predictedETA - this.actualDuration)
      const accuracy = Math.max(0, 100 - (error / this.predictedETA) * 100)
      
      // Calculate distance (simplified)
      const distance = Math.sqrt(
        Math.pow(this.destinationPoint.x - this.startPoint.x, 2) + 
        Math.pow(this.destinationPoint.y - this.startPoint.y, 2)
      ) / 10 // Scale factor for demo
      
      // Create result record
      const result = {
        id: Date.now(),
        timestamp: new Date().toLocaleString(),
        predictedETA: this.predictedETA,
        actualDuration: this.actualDuration,
        distance: distance.toFixed(1),
        accuracy: Math.round(accuracy)
      }
      
      // Add to results
      this.recentResults.unshift(result)
      if (this.recentResults.length > 10) {
        this.recentResults = this.recentResults.slice(0, 10)
      }
      
      // Update statistics
      this.updateStatistics(result)
    },
    
    updateStatistics(newResult) {
      this.statistics.totalRuns++
      this.statistics.totalDistance += parseFloat(newResult.distance)
      
      // Calculate average accuracy
      const totalAccuracy = this.recentResults.reduce((sum, result) => sum + result.accuracy, 0)
      this.statistics.avgAccuracy = Math.round(totalAccuracy / this.recentResults.length)
      
      // Calculate average error
      const totalError = this.recentResults.reduce((sum, result) => {
        return sum + Math.abs(result.predictedETA - result.actualDuration)
      }, 0)
      this.statistics.avgError = Math.round(totalError / this.recentResults.length)
    },
    
    resetPoints() {
      console.log('🔄 Resetting points')
      this.startPoint = null
      this.destinationPoint = null
      this.calculatedRoute = null
      this.resetSimulation()
    },
    
    resetSimulation() {
      this.isSimulationRunning = false
      this.vehiclePosition = null
      this.routePath = null
      this.currentPrediction = null
      this.predictedETA = null
      this.actualDuration = null
      
      // Also reset the points so user can start fresh
      this.startPoint = null
      this.destinationPoint = null
      
      if (this.animationInterval) {
        clearInterval(this.animationInterval)
        this.animationInterval = null
      }
    },
    
    getAccuracyClass(accuracy) {
      if (accuracy >= 90) return 'bg-green-100 text-green-800'
      if (accuracy >= 70) return 'bg-yellow-100 text-yellow-800'
      return 'bg-red-100 text-red-800'
    },
    
    calculateAccuracy() {
      if (!this.predictedETA || !this.actualDuration) return 0
      const error = Math.abs(this.predictedETA - this.actualDuration)
      const accuracy = Math.max(0, 100 - (error / this.predictedETA) * 100)
      return Math.round(accuracy)
    },
    
    getAccuracySummaryClass() {
      const accuracy = this.calculateAccuracy()
      if (accuracy >= 90) return 'bg-green-50'
      if (accuracy >= 70) return 'bg-yellow-50'
      return 'bg-red-50'
    },
    
    getAccuracySummaryTextClass() {
      const accuracy = this.calculateAccuracy()
      if (accuracy >= 90) return 'text-green-600'
      if (accuracy >= 70) return 'text-yellow-600'
      return 'text-red-600'
    },
    
    closeJourneySummary() {
      this.showJourneySummary = false
      // Reset everything for next journey
      this.resetSimulation()
    },
    
    
    
    
    // Real-time vehicle methods
    
    // Simulation playback methods
    async loadSimulationStatus() {
      try {
        const response = await apiService.getSimulationStatus()
        this.simulationStatus = response
        this.isSimulationPlaying = response.is_running || false
        this.simulationTime = response.simulation_time || '00:00:00:00'
      } catch (error) {
        console.error('Error loading simulation status:', error)
      }
    },
    
    // Vehicle management methods
    async loadActiveVehicles() {
      try {
        const response = await apiService.getActiveVehicles()
        this.activeVehicles = response.vehicles || []
        console.log(`Loaded ${this.activeVehicles.length} active vehicles`)
      } catch (error) {
        console.error('Error loading active vehicles:', error)
        this.activeVehicles = []
      }
    },
    
    startVehicleUpdates() {
      // Load vehicles immediately
      this.loadActiveVehicles()
      
      // Set up interval for real-time updates only when simulation is playing
      this.vehicleUpdateInterval = setInterval(() => {
        if (this.isSimulationPlaying) {
          this.loadActiveVehicles()
        }
      }, 1000) // Update every second
      
      console.log('🚗 Started vehicle updates')
    },
    
    stopVehicleUpdates() {
      if (this.vehicleUpdateInterval) {
        clearInterval(this.vehicleUpdateInterval)
        this.vehicleUpdateInterval = null
        console.log('🛑 Stopped vehicle updates')
      }
    },
    
    async startSimulationPlayback() {
      try {
        await apiService.startSimulation()
        this.isSimulationPlaying = true
        this.startSimulationUpdates()
        this.startVehicleUpdates()
        console.log('▶️ Started simulation playback')
      } catch (error) {
        console.error('Error starting simulation playback:', error)
      }
    },
    
    async stopSimulationPlayback() {
      try {
        await apiService.stopSimulation()
        this.isSimulationPlaying = false
        this.stopSimulationUpdates()
        this.stopVehicleUpdates()
        console.log('⏹️ Stopped simulation playback')
      } catch (error) {
        console.error('Error stopping simulation playback:', error)
      }
    },
    
    startSimulationUpdates() {
      // Update simulation status every 2 seconds only when simulation is playing
      this.simulationUpdateInterval = setInterval(async () => {
        if (this.isSimulationPlaying) {
          await this.loadSimulationStatus()
        }
      }, 2000)
    },
    
    stopSimulationUpdates() {
      if (this.simulationUpdateInterval) {
        clearInterval(this.simulationUpdateInterval)
        this.simulationUpdateInterval = null
      }
    }
  },
  
  async mounted() {
    console.log('🚀 DemoPage mounted - starting data loading...')
    await this.loadNetworkData()
    await this.loadSimulationStatus()
    this.startVehicleUpdates()
    this.startSimulationUpdates() // Start simulation status updates
    console.log('✅ DemoPage mounted - data loading completed')
  },
  
  beforeUnmount() {
    if (this.animationInterval) {
      clearInterval(this.animationInterval)
    }
    if (this.simulationUpdateInterval) {
      clearInterval(this.simulationUpdateInterval)
    }
    this.stopVehicleUpdates()
    this.stopSimulationUpdates() // Stop simulation updates
  }
}
</script>

<style scoped>
.road-path {
  pointer-events: stroke;
  transition: all 0.2s ease;
}

.road-path.clickable {
  cursor: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 32 32"><defs><filter id="shadow" x="-50%" y="-50%" width="200%" height="200%"><feDropShadow dx="1" dy="1" stdDeviation="1" flood-color="%23000000" flood-opacity="0.3"/></filter></defs><g filter="url(%23shadow)"><circle cx="16" cy="16" r="14" fill="%23ffffff" stroke="%23374151" stroke-width="2"/><path d="M6 14h20c1.1 0 2 .9 2 2v4c0 1.1-.9 2-2 2H6c-1.1 0-2-.9-2-2v-4c0-1.1.9-2 2-2z" fill="%23dc2626"/><path d="M8 10h16v4H8z" fill="%23fbbf24"/><path d="M10 8h12v2H10z" fill="%23f59e0b"/><circle cx="9" cy="20" r="2.5" fill="%231f2937"/><circle cx="23" cy="20" r="2.5" fill="%231f2937"/><circle cx="9" cy="20" r="1" fill="%236b7280"/><circle cx="23" cy="20" r="1" fill="%236b7280"/><path d="M12 12h8v2h-8z" fill="%23ffffff"/></g></svg>') 11 11, pointer;
}

.road-path:hover {
  stroke: #00bfff !important;
  stroke-width: 50 !important;
}




.road-tooltip {
  animation: fadeIn 0.2s ease-in-out;
}

/* Enhanced road styling for better visibility */
.road-path {
  stroke-linecap: round;
  stroke-linejoin: round;
}


.expressway {
  stroke-dasharray: 5,5;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(5px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
