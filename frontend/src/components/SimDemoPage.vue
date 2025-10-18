<template>
  <div class="app-container">
    <!-- Navigation -->
    <nav class="bg-blue-900 text-white shadow-lg">
      <div class="w-full px-2 xs:px-3 sm:px-4 md:px-6 lg:px-8 xl:px-12 2xl:px-16 3xl:px-20 4xl:px-24">
        <div class="header-grid">
          <!-- Left side - Lab name -->
          <div class="header-left">
            <router-link to="/" class="header-logo">
              SmartTransportation Lab
            </router-link>
          </div>
          
          <!-- Right side - ETA text -->
          <div class="header-right">
            <span class="header-subtitle">
              <span class="header-mobile-text">Real time ETA prediction</span>
              <span class="header-desktop-text">Real time ETA prediction model performance testing</span>
            </span>
          </div>
        </div>
      </div>
    </nav>

    <!-- Main Content Section -->
    <div class="main-content">
      <!-- Landscape Orientation Message (Desktop/Landscape) -->
      <div class="landscape-message">
        <div class="landscape-content">
          <div class="phone-icon">📱</div>
          <h2>Please Rotate Your Device</h2>
          <p>For the best simulation experience, please rotate your device to portrait orientation.</p>
          <div class="rotation-hint">
            <div class="arrow">↻</div>
            <span>Turn your device upright</span>
          </div>
        </div>
      </div>

      <!-- Simulation Layout (Portrait Only) -->
      <div class="simulation-layout">
        <div class="content-grid">
          <!-- Analysis Section - 20% -->
          <div class="analysis-section">
            <div class="section-placeholder">
              <h3>Analysis Section</h3>
              <p>20% width</p>
            </div>
          </div>
          
          <!-- Map Section - 60% -->
          <div class="map-section">
            <!-- SUMO Network Container -->
            <div 
              class="map-container"
              ref="mapContainer"
            >
              <!-- SUMO Network Visualization -->
              <svg 
                ref="networkSvg"
                :viewBox="svgViewBox" 
                width="100%" 
                height="100%" 
                class="absolute inset-0 cursor-crosshair map-container" 
                style="background: #f1f5f9;"
                preserveAspectRatio="xMidYMid meet"
                @mousemove="handleMouseMove"
                @click="handleMapClick"
                @touchstart="handleTouchStart"
                @touchmove="handleTouchMove"
                @touchend="handleTouchEnd"
              >

                <!-- SUMO Network Edges (Roads) -->
                <g v-if="networkData && networkData.edges">
                  <template v-for="edge in networkData.edges" :key="edge.id">
                    <!-- Skip rendering E5 and E6 edges only -->
                    <template v-if="edge.id === 'E5' || edge.id === 'E6'"></template>
                    <template v-else>
                      <!-- Use path for express edges with detailed shape, line for regular roads -->
                      <path 
                        v-if="isExpressEdge(edge) && edge.shape_points && edge.shape_points.length > 0 && getPathData(edge.shape_points)"
                        :d="getPathData(edge.shape_points)"
                        :stroke="getRouteStrokeColor(edge)"
                        :stroke-width="getRouteStrokeWidth(edge)"
                        :opacity="getRoadOpacity(edge)"
                        :class="getRoadClass(edge)"
                        :data-road-name="edge.id"
                        fill="none"
                        @click="handleEdgeClick(edge, $event)"
                        @touchstart="handleEdgeClick(edge, $event)"
                      />
                      <!-- Fallback to line if path data is invalid -->
                      <line 
                        v-else-if="isExpressEdge(edge)"
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
                        @touchstart="handleEdgeClick(edge, $event)"
                      />
                      <!-- Regular roads -->
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
                        @touchstart="handleEdgeClick(edge, $event)"
                      />
                      
                      <!-- Invisible clickable areas for easier selection -->
                      <path 
                        v-if="isExpressEdge(edge) && edge.shape_points && edge.shape_points.length > 0 && getPathData(edge.shape_points)"
                        :d="getPathData(edge.shape_points)"
                        stroke="transparent" 
                        :stroke-width="60"
                        fill="none"
                        :class="getRoadClass(edge)"
                        :data-road-name="edge.id"
                        @click="handleEdgeClick(edge, $event)"
                        @touchstart="handleEdgeClick(edge, $event)"
                      />
                      <!-- Fallback invisible clickable line -->
                      <line 
                        v-else-if="isExpressEdge(edge)"
                        :x1="getJunctionPosition(edge.from_junction)?.x || 0"
                        :y1="getJunctionPosition(edge.from_junction)?.y || 0"
                        :x2="getJunctionPosition(edge.to_junction)?.x || 0"
                        :y2="getJunctionPosition(edge.to_junction)?.y || 0"
                        stroke="transparent"
                        :stroke-width="60"
                        :class="getRoadClass(edge)"
                        :data-road-name="edge.id"
                        @click="handleEdgeClick(edge, $event)"
                        @touchstart="handleEdgeClick(edge, $event)"
                      />
                      <line 
                        v-else
                        :x1="getJunctionPosition(edge.from_junction)?.x || 0"
                        :y1="getJunctionPosition(edge.from_junction)?.y || 0"
                        :x2="getJunctionPosition(edge.to_junction)?.x || 0"
                        :y2="getJunctionPosition(edge.to_junction)?.y || 0"
                        stroke="transparent"
                        :stroke-width="60"
                        :class="getRoadClass(edge)"
                        :data-road-name="edge.id"
                        @click="handleEdgeClick(edge, $event)"
                        @touchstart="handleEdgeClick(edge, $event)"
                      />
                    </template>
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
                  stroke="#00ff00" 
                  stroke-width="8" 
                  fill="none" 
                  opacity="0.9"
                  class="route-path"
                />
                
                <!-- Real Vehicles from Simulation -->
                <g v-if="activeVehicles && activeVehicles.length > 0">
                  <!-- Regular vehicles (circles) -->
                  <circle 
                    v-for="vehicle in activeVehicles.filter(v => !isNaN(v.x) && !isNaN(v.y) && v.type !== 'user_defined')"
                    :key="vehicle.id"
                    :cx="vehicle.x"
                    :cy="vehicle.y"
                    r="36"
                    :fill="getVehicleColor(vehicle.type, vehicle.status)"
                    stroke="#000000"
                    stroke-width="3"
                    class="vehicle-marker"
                    opacity="0.8"
                  />
                  <!-- User-defined vehicles (sports car image) -->
                  <g 
                    v-for="vehicle in activeVehicles.filter(v => !isNaN(v.x) && !isNaN(v.y) && v.type === 'user_defined')"
                    :key="vehicle.id"
                    :transform="getVehicleTransform(vehicle)"
                    class="vehicle-marker"
                    opacity="0.8"
                  >
                    <image 
                      :x="-216" 
                      :y="-108" 
                      width="432" 
                      height="216" 
                      href="/images/car.png"
                      preserveAspectRatio="xMidYMid meet"
                    />
                  </g>
              </g>
            </svg>

            <!-- Desktop/Tablet Landscape Layout - Positioned 25% towards left -->
            <div class="hidden sm:block absolute top-4 left-1/4 transform -translate-x-2/3 pointer-events-none z-10 landscape-only">
              <div class="bg-white bg-opacity-70 rounded-xl shadow-xl p-4 text-center max-w-xs animate-fade-in">
                <div class="text-2xl mb-2 animate-bounce">
                  <span v-if="!startPoint">📍</span>
                  <span v-else-if="!destinationPoint">🎯</span>
                  <span v-else-if="!isJourneyRunning">🚀</span>
                  <span v-else>🚗</span>
                </div>
                <h3 class="text-lg font-bold text-gray-800 mb-1">
                  <span v-if="!startPoint">Set Starting Point</span>
                  <span v-else-if="!destinationPoint">Set Destination</span>
                  <span v-else-if="!isJourneyRunning">Ready to Start!</span>
                  <span v-else>Journey in Progress</span>
                </h3>
                <p class="text-sm text-gray-600">
                  {{ getInstructionText() }}
                </p>
              </div>
            </div>

            <!-- Map Legend -->
            <div v-if="showLegend" class="absolute top-2 left-2 sm:top-4 sm:left-4 bg-white bg-opacity-95 rounded-lg shadow-lg pointer-events-auto animate-fade-in hidden sm:block z-20" style="max-width: 180px;">
              <!-- Legend Header (Always Visible) -->
              <div 
                @click="toggleLegend"
                class="flex items-center justify-between cursor-pointer hover:bg-gray-50 rounded-t-lg transition-colors"
                :class="legendCollapsed ? 'p-2' : 'p-3'"
              >
                <h3 class="font-bold text-gray-800 flex items-center"
                    :class="legendCollapsed ? 'text-xs' : 'text-sm'">
                  <span :class="legendCollapsed ? 'mr-0.5' : 'mr-1'">🗺️</span>
                  <span v-if="!legendCollapsed">Legend</span>
                </h3>
                <span class="text-gray-500 text-xs transform transition-transform" 
                      :class="{ 'rotate-180': !legendCollapsed }">
                  ▼
                </span>
              </div>
              
              <!-- Collapsible Content -->
              <div v-if="!legendCollapsed" class="px-3 pb-3">
                <!-- Roads Section -->
                <div class="mb-3">
                  <h4 class="text-xs font-semibold text-gray-700 mb-1">Roads</h4>
                  <div class="space-y-1">
                    <div class="flex items-center">
                      <div class="w-4 h-0.5 bg-gray-600 mr-2"></div>
                      <span class="text-xs text-gray-600">Regular</span>
                    </div>
                    <div class="flex items-center">
                      <svg class="w-4 h-0.5 mr-2" viewBox="0 0 16 2">
                        <line x1="0" y1="1" x2="16" y2="1" stroke="#1e40af" stroke-width="1" opacity="0.6" stroke-dasharray="2,2"/>
                      </svg>
                      <span class="text-xs text-gray-600">Expressways</span>
                    </div>
                    <div class="flex items-center">
                      <div class="w-4 h-1 bg-green-500 mr-2"></div>
                      <span class="text-xs text-gray-600">Route</span>
                    </div>
                  </div>
                </div>

                <!-- Markers Section -->
                <div class="mb-3">
                  <h4 class="text-xs font-semibold text-gray-700 mb-1">Markers</h4>
                  <div class="space-y-1">
                    <div class="flex items-center">
                      <div class="w-3 h-3 bg-green-500 rounded-full mr-2 border border-white"></div>
                      <span class="text-xs text-gray-600">Start (S)</span>
                    </div>
                    <div class="flex items-center">
                      <div class="w-3 h-3 bg-red-500 rounded-full mr-2 border border-white"></div>
                      <span class="text-xs text-gray-600">Dest (D)</span>
                    </div>
                  </div>
                </div>

                <!-- Vehicles Section -->
                <div class="mb-3">
                  <h4 class="text-xs font-semibold text-gray-700 mb-1">Vehicles</h4>
                  <div class="space-y-1">
                    <div class="flex items-center">
                      <div class="w-3 h-3 bg-blue-500 rounded-full mr-2 border border-black"></div>
                      <span class="text-xs text-gray-600">Cars</span>
                    </div>
                    <div class="flex items-center">
                      <div class="w-3 h-3 bg-orange-500 rounded-full mr-2 border border-black"></div>
                      <span class="text-xs text-gray-600">Buses</span>
                    </div>
                    <div class="flex items-center">
                      <div class="w-3 h-3 bg-green-500 rounded-full mr-2 border border-black"></div>
                      <span class="text-xs text-gray-600">Trucks</span>
                    </div>
                    <div class="flex items-center">
                      <svg class="w-3 h-3 mr-2" viewBox="0 0 12 12">
                        <path d="M6 1l1.5 3L12 4.5l-2.5 2.5L11 11l-3-1.5L5 11l1-4L3 4.5l3.5-.5L6 1z" fill="#fbbf24" stroke="#000000" stroke-width="0.3"/>
                      </svg>
                      <span class="text-xs text-gray-600">Your Vehicle</span>
                    </div>
                    <div class="flex items-center">
                      <div class="w-3 h-3 bg-white rounded-full mr-2 border border-black"></div>
                      <span class="text-xs text-gray-600">Not Tracked</span>
                    </div>
                  </div>
                </div>

              </div>
            </div>

            <!-- Control Buttons - Top Right Overlay -->
            <div class="absolute top-2 right-2 sm:top-4 sm:right-4 z-20 pointer-events-auto">
              <div class="flex flex-col items-stretch gap-1 sm:gap-2 sm:flex-row sm:items-center">
                <!-- Start Journey Button - Show when both points are set -->
                <button 
                  v-if="startPoint && destinationPoint"
                  @click="handleMainButtonClick()"
                  :class="getMainButtonClass()"
                  class="text-white px-2 py-1 sm:px-4 sm:py-2 rounded-md sm:rounded-lg font-semibold transition duration-300 text-xs sm:text-sm shadow-lg"
                >
                  {{ getMainButtonText() }}
                </button>
                
                <!-- Reset Points Button - Show when points are selected but journey not running -->
                <button 
                  v-if="startPoint && !isJourneyRunning"
                  @click="resetPoints"
                  class="bg-gray-600 hover:bg-gray-700 text-white px-2 py-1 sm:px-4 sm:py-2 rounded-md sm:rounded-lg font-semibold transition duration-300 text-xs sm:text-sm shadow-lg"
                >
                  🔄 Reset Points
                </button>
              </div>
            </div>
          </div>
        </div>
          
          <!-- Results Section - 20% -->
          <div class="results-section">
            <div class="section-placeholder">
              <h3>Results Section</h3>
              <p>20% width</p>
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
  name: 'SimDemoPage',
  data() {
    return {
      // Responsive state management
      viewport: {
        width: 0,
        height: 0,
        isMobile: false,
        isTablet: false,
        isDesktop: false,
        isUltraWide: false,
        orientation: 'portrait',
        pixelRatio: 1,
        isRetina: false
      },
      
      // Responsive breakpoints
      breakpoints: {
        xs: 320,
        sm: 640,
        md: 768,
        lg: 1024,
        xl: 1280,
        '2xl': 1536,
        '3xl': 1920,
        '4xl': 2560,
        '5xl': 3440,
        '6xl': 3840
      },
      
      // Map-related data
      mousePosition: { x: 0, y: 0 },
      startPoint: null,
      destinationPoint: null,
      isJourneyRunning: false,
      
      // Network visualization
      networkData: null,
      networkBounds: null,
      svgViewBox: "0 0 1000 1000",
      
      // Simulation playback
      isSimulationPlaying: false,
      simulationStatus: {
        vehicles: 0,
        vehicles_in_route: 0,
        trips_added: 0,
        current_step: 0
      },
      
      // Vehicle management
      activeVehicles: [],
      vehicleUpdateInterval: null,
      
      // Legend visibility
      showLegend: true,
      legendCollapsed: false,
      legendAutoFoldTimer: null,
      
      // Results tracking
      vehicleResults: [], // Array of vehicle journey results
      maxResults: 20, // Maximum number of results to keep
      
      // Route data
      routePath: null,
      routeEdges: null,
      routeDistance: null,
      routeDuration: null,
      
      // Animation intervals
      simulationUpdateInterval: null
    }
  },
  methods: {
    // Responsive utilities
    updateViewport() {
      this.viewport.width = window.innerWidth
      this.viewport.height = window.innerHeight
      this.viewport.pixelRatio = window.devicePixelRatio || 1
      this.viewport.isRetina = this.viewport.pixelRatio > 1
      this.viewport.orientation = window.innerHeight > window.innerWidth ? 'portrait' : 'landscape'
      
      // Determine device type
      this.viewport.isMobile = this.viewport.width < this.breakpoints.md
      this.viewport.isTablet = this.viewport.width >= this.breakpoints.md && this.viewport.width < this.breakpoints.lg
      this.viewport.isDesktop = this.viewport.width >= this.breakpoints.lg && this.viewport.width < this.breakpoints['3xl']
      this.viewport.isUltraWide = this.viewport.width >= this.breakpoints['3xl']
    },
    
    // Get current breakpoint
    getCurrentBreakpoint() {
      const width = this.viewport.width
      if (width < this.breakpoints.xs) return 'xs'
      if (width < this.breakpoints.sm) return 'sm'
      if (width < this.breakpoints.md) return 'md'
      if (width < this.breakpoints.lg) return 'lg'
      if (width < this.breakpoints.xl) return 'xl'
      if (width < this.breakpoints['2xl']) return '2xl'
      if (width < this.breakpoints['3xl']) return '3xl'
      if (width < this.breakpoints['4xl']) return '4xl'
      if (width < this.breakpoints['5xl']) return '5xl'
      return '6xl'
    },
    
    // Responsive class helper
    getResponsiveClasses(baseClasses = '') {
      const breakpoint = this.getCurrentBreakpoint()
      const orientation = this.viewport.orientation
      const isRetina = this.viewport.isRetina
      
      let classes = baseClasses
      
      // Add breakpoint-specific classes
      classes += ` breakpoint-${breakpoint}`
      
      // Add orientation classes
      classes += ` orientation-${orientation}`
      
      // Add retina class
      if (isRetina) classes += ' retina'
      
      // Add device type classes
      if (this.viewport.isMobile) classes += ' mobile'
      if (this.viewport.isTablet) classes += ' tablet'
      if (this.viewport.isDesktop) classes += ' desktop'
      if (this.viewport.isUltraWide) classes += ' ultra-wide'
      
      return classes
    },
    
    // Handle resize with debouncing
    handleResize() {
      clearTimeout(this.resizeTimeout)
      this.resizeTimeout = setTimeout(() => {
        this.updateViewport()
        this.onViewportChange()
      }, 100)
    },
    
    // Called when viewport changes
    onViewportChange() {
      // Override this method in your components for custom responsive behavior
      console.log('Viewport changed:', this.viewport)
    },
    
    // Map methods
    async loadNetworkData() {
      try {
        console.log('🔄 Loading network data...')
        const response = await apiService.getNetworkData()
        
        if (response) {
          this.networkData = response
          this.networkBounds = response.bounds
          
          // Calculate optimal viewBox with asymmetric padding
          const paddingX = 0.02 // 2% padding on sides
          const paddingY = 0.01 // 1% padding on top and bottom
          const width = this.networkBounds.max_x - this.networkBounds.min_x
          const height = this.networkBounds.max_y - this.networkBounds.min_y
          const paddingXValue = width * paddingX
          const paddingYValue = height * paddingY
          
          this.svgViewBox = `${this.networkBounds.min_x - paddingXValue} ${this.networkBounds.min_y - paddingYValue} ${width + 2 * paddingXValue} ${height + 2 * paddingYValue}`
          
          console.log('✅ Network data loaded successfully:', {
            edges: this.networkData?.edges?.length || 0,
            junctions: this.networkData?.junctions?.length || 0,
            bounds: this.networkBounds,
            viewBox: this.svgViewBox
          })
        } else {
          console.error('❌ Failed to load network data: No response')
        }
      } catch (error) {
        console.error('❌ Error loading network data:', error)
        this.networkData = null
      }
    },
    
    
    getJunctionPosition(junctionId) {
      if (!this.networkData || !this.networkData.junctions) return null
      return this.networkData.junctions.find(j => j.id === junctionId)
    },
    
    isExpressEdge(edge) {
      return edge.id && (edge.id.startsWith('-E') || edge.id.startsWith('E'))
    },
    
    getPathData(shapePoints) {
      if (!shapePoints || shapePoints.length < 2) return ''
      
      let pathData = `M ${shapePoints[0][0]} ${shapePoints[0][1]}`
      for (let i = 1; i < shapePoints.length; i++) {
        pathData += ` L ${shapePoints[i][0]} ${shapePoints[i][1]}`
      }
      return pathData
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
      // Check if this edge is part of the calculated route (only intermediate edges)
      if (!this.routeEdges || !Array.isArray(this.routeEdges)) return false
      
      const edgeIndex = this.routeEdges.indexOf(edge.id)
      // Only highlight intermediate edges (skip first and last)
      return edgeIndex > 0 && edgeIndex < this.routeEdges.length - 1
    },
    
    getRouteStrokeColor(edge) {
      // Return bright fluorescent green for route edges
      if (this.isRouteEdge(edge)) {
        return "#00ff00"  // Bright green
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
        return "40"  // Extra thick for route
      }
      
      return this.getRoadStrokeWidth(edge)
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
        case 'user_defined':
          return '#dc2626'  // Red
        default:
          return '#6b7280'  // Gray
      }
    },
    

    getVehicleTransform(vehicle) {
      // Simple positioning - no rotation
      return `translate(${vehicle.x}, ${vehicle.y})`
    },

    
    handleMapClick(event) {
      // Only show overlay if simulation is running and clicking on empty SVG area
      if ((this.isSimulationPlaying || this.isJourneyRunning) && event.target.tagName === 'svg') {
        console.log('🚗 Simulation running - showing overlay on map click')
      }
    },
    
    handleMouseMove(event) {
      const svg = this.$refs.networkSvg
      if (!svg) return

      const rect = svg.getBoundingClientRect()
      this.mousePosition = {
        x: event.clientX - rect.left,
        y: event.clientY - rect.top
      }
    },
    
    handleTouchStart(event) {
      event.preventDefault()
      if (event.touches.length === 1) {
        const touch = event.touches[0]
        const svg = this.$refs.networkSvg
        if (!svg) return

        const rect = svg.getBoundingClientRect()
        this.mousePosition = {
          x: touch.clientX - rect.left,
          y: touch.clientY - rect.top
        }
      }
    },
    
    handleTouchMove(event) {
      event.preventDefault()
      if (event.touches.length === 1) {
        const touch = event.touches[0]
        const svg = this.$refs.networkSvg
        if (!svg) return

        const rect = svg.getBoundingClientRect()
        this.mousePosition = {
          x: touch.clientX - rect.left,
          y: touch.clientY - rect.top
        }
      }
    },
    
    handleTouchEnd(event) {
      event.preventDefault()
      if (event.changedTouches.length === 1) {
        const touch = event.changedTouches[0]
        const svg = this.$refs.networkSvg
        if (!svg) return

        const rect = svg.getBoundingClientRect()
        const clickEvent = {
          clientX: touch.clientX,
          clientY: touch.clientY,
          target: svg
        }
        
        this.handleMapClick(clickEvent)
      }
    },
    
    handleEdgeClick(edge, event) {
      console.log('🔍 handleEdgeClick called:', {
        edgeId: edge.id,
        eventType: event.type,
        isSimulationPlaying: this.isSimulationPlaying,
        isJourneyRunning: this.isJourneyRunning
      })
      
      event.preventDefault()
      event.stopPropagation()
      
      if (this.isSimulationPlaying || this.isJourneyRunning) {
        return
      }
      
      // Calculate the exact middle position of the edge
      let x, y
      
      if (edge.shape_points && edge.shape_points.length > 0) {
        const totalLength = edge.shape_points.length
        const midIndex = Math.floor(totalLength / 2)
        
        if (totalLength % 2 === 0 && midIndex > 0) {
          const point1 = edge.shape_points[midIndex - 1]
          const point2 = edge.shape_points[midIndex]
          x = (point1[0] + point2[0]) / 2
          y = (point1[1] + point2[1]) / 2
        } else {
          x = edge.shape_points[midIndex][0]
          y = edge.shape_points[midIndex][1]
        }
      } else {
        const fromJunction = this.getJunctionPosition(edge.from_junction)
        const toJunction = this.getJunctionPosition(edge.to_junction)
        if (fromJunction && toJunction) {
          x = (fromJunction.x + toJunction.x) / 2
          y = (fromJunction.y + toJunction.y) / 2
        } else {
          x = 0
          y = 0
        }
      }
      
      if (!this.startPoint) {
        this.startPoint = { id: edge.id, x, y }
        console.log('📍 Start point set:', this.startPoint)
      } else if (!this.destinationPoint) {
        this.destinationPoint = { id: edge.id, x, y }
        console.log('📍 Destination point set:', this.destinationPoint)
        this.calculateAndDisplayRoute()
      }
    },
    
    async calculateAndDisplayRoute() {
      if (!this.startPoint || !this.destinationPoint) return
      
      console.log('🛣️ Calculating route from', this.startPoint.id, 'to', this.destinationPoint.id)
      
      try {
        // Calculate route between edges
        const routeResponse = await apiService.calculateRouteByEdges(
          this.startPoint.id, 
          this.destinationPoint.id
        )
        
        if (routeResponse.error) {
          console.error('❌ Route calculation failed:', routeResponse.error)
          alert(`Route calculation failed: ${routeResponse.error}`)
          return
        }
        
        console.log('✅ Route calculated:', routeResponse)
        
        // Store the route for display
        this.routeEdges = routeResponse.edges
        this.routeDistance = routeResponse.distance
        this.routeDuration = routeResponse.duration
        
        // Generate SVG path for the route
        this.routePath = this.generateRoutePath(this.routeEdges)
        
        console.log('🟢 Route displayed on map - Edges:', this.routeEdges.join(', '))
        
      } catch (error) {
        console.error('❌ Error calculating route:', error)
        alert('Failed to calculate route. Please try again.')
      }
    },
    
    generateRoutePath(edges) {
      if (!edges || edges.length === 0) return ''
      
      let pathData = ''
      let isFirst = true
      
      for (const edgeId of edges) {
        const edge = this.networkData.edges.find(e => e.id === edgeId)
        if (!edge) continue
        
        if (edge.shape_points && edge.shape_points.length > 0) {
          if (isFirst) {
            pathData = `M ${edge.shape_points[0][0]} ${edge.shape_points[0][1]}`
            isFirst = false
          }
          for (let i = 1; i < edge.shape_points.length; i++) {
            pathData += ` L ${edge.shape_points[i][0]} ${edge.shape_points[i][1]}`
          }
        } else {
          const fromJunction = this.getJunctionPosition(edge.from_junction)
          const toJunction = this.getJunctionPosition(edge.to_junction)
          if (fromJunction && toJunction) {
            if (isFirst) {
              pathData = `M ${fromJunction.x} ${fromJunction.y}`
              isFirst = false
            }
            pathData += ` L ${toJunction.x} ${toJunction.y}`
          }
        }
      }
      
      return pathData
    },
    
    resetPoints() {
      this.startPoint = null
      this.destinationPoint = null
      this.routePath = null
      this.routeEdges = null
      this.routeDistance = null
      this.routeDuration = null
      console.log('🔄 Points reset')
    },
    
    handleMainButtonClick() {
      this.startJourney()
    },
    
    getMainButtonClass() {
      return 'bg-blue-600 hover:bg-blue-700'
    },
    
    getMainButtonText() {
      return '▶️ Start Journey'
    },
    
    async startJourney() {
      if (!this.startPoint || !this.destinationPoint) return
      
      console.log('🚀 Starting journey from', this.startPoint, 'to', this.destinationPoint)
      
      try {
        // Ensure route is calculated before starting journey
        if (!this.routeEdges || !Array.isArray(this.routeEdges)) {
          console.log('🔄 Route not calculated yet, calculating now...')
          await this.calculateAndDisplayRoute()
          
          // Check if route calculation was successful
          if (!this.routeEdges || !Array.isArray(this.routeEdges)) {
            console.error('❌ Route calculation failed')
            alert('Failed to calculate route. Please try selecting different points.')
            return
          }
        }
        
        console.log('🛣️ Route edges available:', this.routeEdges)
        
        // Convert Proxy array to plain JavaScript array
        const routeEdgesArray = Array.from(this.routeEdges)
        console.log('🛣️ Route edges array:', routeEdgesArray)
        
        // Call the regular API to add vehicle to simulation
        console.log('🚀 Calling apiService.startJourney with:', {
          startEdge: this.startPoint.id,
          endEdge: this.destinationPoint.id,
          routeEdges: routeEdgesArray,
          routeEdgesType: typeof routeEdgesArray,
          routeEdgesLength: routeEdgesArray.length,
          routeEdgesIsArray: Array.isArray(routeEdgesArray)
        })
        
        const response = await apiService.startJourney(
          this.startPoint.id,
          this.destinationPoint.id,
          routeEdgesArray
        )
        
        console.log('✅ Journey started:', response)
        
        // Add vehicle result to local tracking
        this.addVehicleResult(
          response.vehicle_id, 
          response.start_time, 
          response.start_time_string, 
          response.distance, 
          response.predicted_eta,
          this.startPoint.id,
          this.destinationPoint.id,
          routeEdgesArray
        )
        
        // Start simulation with additional vehicle
          this.startSimulationPlayback()
        this.isJourneyRunning = true
        
        console.log('🚗 Vehicle added to simulation with route')
      } catch (error) {
        console.error('❌ Error starting journey:', error)
        
        // Try to get more detailed error information
        let errorMessage = 'Failed to start journey. Please try again.'
        if (error.response) {
          // Server responded with error status
          console.error('Server error response:', error.response.data)
          errorMessage = `Server error: ${error.response.status} - ${error.response.data?.detail || error.response.data?.message || 'Unknown error'}`
        } else if (error.request) {
          // Request was made but no response received
          console.error('No response received:', error.request)
          errorMessage = 'No response from server. Please check if the backend is running.'
        } else {
          // Something else happened
          console.error('Request setup error:', error.message)
          errorMessage = `Request error: ${error.message}`
        }
        
        alert(errorMessage)
      }
    },

    async calculateAndDisplayRoute() {
      if (!this.startPoint || !this.destinationPoint) return
      
      console.log('🛣️ Calculating route from', this.startPoint.id, 'to', this.destinationPoint.id)
      
      try {
        // Calculate route between edges
        const routeResponse = await apiService.calculateRouteByEdges(
          this.startPoint.id, 
          this.destinationPoint.id
        )
        
        if (routeResponse.error) {
          console.error('❌ Route calculation failed:', routeResponse.error)
          alert(`Route calculation failed: ${routeResponse.error}`)
          return
        }
        
        console.log('✅ Route calculated:', routeResponse)
        
        // Store the route for display
        this.routeEdges = routeResponse.edges
        this.routeDistance = routeResponse.distance
        this.routeDuration = routeResponse.duration
        
        // Generate SVG path for the route
        this.routePath = this.generateRoutePath(this.routeEdges)
        
        console.log('🟢 Route displayed on map - Edges:', this.routeEdges.join(', '))
        
      } catch (error) {
        console.error('❌ Error calculating route:', error)
        alert('Failed to calculate route. Please try again.')
      }
    },

    generateRoutePath(routeEdges) {
      if (!routeEdges || routeEdges.length < 2) return ''
      
      try {
        let pathData = ''
        
        // Start from S marker to beginning of second edge
        if (routeEdges.length >= 2) {
          const firstEdge = this.networkData?.edges?.find(e => e.id === routeEdges[0])
          const secondEdge = this.networkData?.edges?.find(e => e.id === routeEdges[1])
          
          if (firstEdge && secondEdge) {
            // Start at S marker (center of first edge)
            const startPoint = this.getEdgeCenterPoint(firstEdge)
            pathData = `M ${startPoint[0]} ${startPoint[1]}`
            
            // Go to the junction that connects to the second edge
            const firstEdgeEndJunction = this.getJunctionPosition(firstEdge.to_junction)
            if (firstEdgeEndJunction) {
              pathData += ` L ${firstEdgeEndJunction.x} ${firstEdgeEndJunction.y}`
            }
          }
        }
        
        // Paint intermediate edges (skip first and last)
        for (let i = 1; i < routeEdges.length - 1; i++) {
          const edgeId = routeEdges[i]
          const edge = this.networkData?.edges?.find(e => e.id === edgeId)
          if (!edge) continue
          
          // Paint the full edge shape
          if (edge.shape_points && edge.shape_points.length > 0) {
            for (const point of edge.shape_points) {
              pathData += ` L ${point[0]} ${point[1]}`
            }
        } else {
            // For edges without shape points, connect the junctions
            const startJunction = this.getJunctionPosition(edge.from_junction)
            const endJunction = this.getJunctionPosition(edge.to_junction)
            if (startJunction && endJunction) {
              pathData += ` L ${startJunction.x} ${startJunction.y}`
              pathData += ` L ${endJunction.x} ${endJunction.y}`
            }
          }
        }
        
        // Paint from end of second-to-last edge to D marker
        if (routeEdges.length >= 2) {
          const secondToLastEdge = this.networkData?.edges?.find(e => e.id === routeEdges[routeEdges.length - 2])
          const lastEdge = this.networkData?.edges?.find(e => e.id === routeEdges[routeEdges.length - 1])
          
          if (secondToLastEdge && lastEdge) {
            // Go to the junction that connects to the last edge
            const secondToLastEndJunction = this.getJunctionPosition(secondToLastEdge.to_junction)
            if (secondToLastEndJunction) {
              pathData += ` L ${secondToLastEndJunction.x} ${secondToLastEndJunction.y}`
            }
            
            // Go to D marker (center of last edge)
            const endPoint = this.getEdgeCenterPoint(lastEdge)
            pathData += ` L ${endPoint[0]} ${endPoint[1]}`
          }
        }
        
        console.log('🛣️ Generated route path:', pathData)
        return pathData
        
      } catch (error) {
        console.error('❌ Error generating route path:', error)
        return ''
      }
    },

    getEdgeCenterPoint(edge) {
      if (edge.shape_points && edge.shape_points.length > 0) {
        // For express edges with shape points, use the middle of the shape
        const midIndex = Math.floor(edge.shape_points.length / 2)
        if (edge.shape_points.length % 2 === 0 && midIndex > 0) {
          const point1 = edge.shape_points[midIndex - 1]
          const point2 = edge.shape_points[midIndex]
          return [(point1[0] + point2[0]) / 2, (point1[1] + point2[1]) / 2]
        } else {
          return [edge.shape_points[midIndex][0], edge.shape_points[midIndex][1]]
        }
      } else {
        // For regular edges, use the midpoint between junctions
        const fromJunction = this.getJunctionPosition(edge.from_junction)
        const toJunction = this.getJunctionPosition(edge.to_junction)
        if (fromJunction && toJunction) {
          return [(fromJunction.x + toJunction.x) / 2, (fromJunction.y + toJunction.y) / 2]
        }
        return [0, 0] // Fallback
      }
    },

    addVehicleResult(vehicleId, startTime, startTimeString, distance, predictedEta, startEdge = null, endEdge = null, routeEdges = null) {
      const result = {
        vehicle_id: vehicleId,
        start_time: startTime,
        start_time_string: startTimeString,
        distance: distance,
        predicted_eta: predictedEta,
        start_edge: startEdge,
        end_edge: endEdge,
        route_edges: routeEdges,
        status: 'running',
        end_time: null,
        end_time_string: null,
        actual_duration: null,
        absolute_error: null,
        accuracy: null
      }
      
      // Add to beginning of array (most recent first)
      this.vehicleResults.unshift(result)
      
      // Keep only maxResults
      if (this.vehicleResults.length > this.maxResults) {
        this.vehicleResults = this.vehicleResults.slice(0, this.maxResults)
      }
      
      console.log('📊 Vehicle result added:', result)
    },
    
    
    startSimulationPlayback() {
      this.isSimulationPlaying = true
      this.simulationUpdateInterval = setInterval(() => {
        this.updateSimulationStatus()
      }, 1000)
    },
    
    stopSimulationPlayback() {
      this.isSimulationPlaying = false
      if (this.simulationUpdateInterval) {
        clearInterval(this.simulationUpdateInterval)
        this.simulationUpdateInterval = null
      }
    },
    
    async updateSimulationStatus() {
      try {
        const response = await apiService.getSimulationStatus()
        if (response.success) {
          this.simulationStatus = response.data
        }
      } catch (error) {
        console.error('❌ Error updating simulation status:', error)
      }
    },
    
    // Vehicle management methods
    startVehicleUpdates() {
      this.vehicleUpdateInterval = setInterval(() => {
        this.loadActiveVehicles()
      }, 1000) // Update every second
    },
    
    stopVehicleUpdates() {
      if (this.vehicleUpdateInterval) {
        clearInterval(this.vehicleUpdateInterval)
        this.vehicleUpdateInterval = null
      }
    },
    
    async loadActiveVehicles() {
      try {
        const response = await apiService.getActiveVehicles()
        
        if (response && response.vehicles && Array.isArray(response.vehicles)) {
          this.activeVehicles = response.vehicles
        } else if (response && Array.isArray(response)) {
          this.activeVehicles = response
        }
      } catch (error) {
        console.error('❌ Error loading active vehicles:', error)
      }
    },
    
    startLegendAutoFold() {
      // Clear any existing timer
      if (this.legendAutoFoldTimer) {
        clearTimeout(this.legendAutoFoldTimer)
      }
      
      // Set timer to collapse legend after 10 seconds
      this.legendAutoFoldTimer = setTimeout(() => {
        this.legendCollapsed = true
        console.log('🕐 Legend auto-folded after 10 seconds')
      }, 10000)
    },
    
    resetLegendAutoFold() {
      // Clear existing timer
      if (this.legendAutoFoldTimer) {
        clearTimeout(this.legendAutoFoldTimer)
      }
      
      // Start new timer
      this.startLegendAutoFold()
    },
    
    toggleLegend() {
      this.legendCollapsed = !this.legendCollapsed
      
      // Reset auto-fold timer when user manually toggles
      this.resetLegendAutoFold()
    },
    
    getInstructionText() {
      if (!this.startPoint) {
        return "Click on a road"
      } else if (!this.destinationPoint) {
        return "Click on a road"
      } else if (!this.isJourneyRunning) {
        return "Click 'Start Journey'"
      } else {
        return "Traveling to destination..."
      }
    },
    
    // Ready for your methods
  },
  mounted() {
    // Initialize viewport
    this.updateViewport()
    
    // Add resize listener
    window.addEventListener('resize', this.handleResize)
    window.addEventListener('orientationchange', this.handleResize)
    
    // Add visibility change listener for performance
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden) {
        this.updateViewport()
      }
    })
    
    // Load network data for the map
    this.loadNetworkData()
    
    // Load vehicles immediately and start updates
    this.loadActiveVehicles()
    this.startVehicleUpdates()
    
    // Start legend auto-fold timer
    this.startLegendAutoFold()
  },
  beforeUnmount() {
    // Clean up listeners
    window.removeEventListener('resize', this.handleResize)
    window.removeEventListener('orientationchange', this.handleResize)
    document.removeEventListener('visibilitychange', this.updateViewport)
    
    if (this.resizeTimeout) {
      clearTimeout(this.resizeTimeout)
    }
    
    // Clean up legend auto-fold timer
    if (this.legendAutoFoldTimer) {
      clearTimeout(this.legendAutoFoldTimer)
      this.legendAutoFoldTimer = null
    }
    
    // Clean up intervals
    this.stopVehicleUpdates()
    this.stopSimulationPlayback()
  }
}
</script>

<style scoped>
/* ===== APP CONTAINER ===== */
.app-container {
  height: 100vh;
  width: 100vw;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  margin: 0;
  padding: 0;
}

/* Prevent scroll bars for this component */

/* Responsive utilities and edge case handling */

/* ===== HEADER GRID LAYOUT ===== */
.header-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  align-items: center;
  height: 2.1rem;
  width: 100%;
  max-width: 100%;
}

@media (min-width: 320px) {
  .header-grid {
    height: 2.45rem;
  }
}

@media (min-width: 640px) {
  .header-grid {
    height: 2.8rem;
  }
}

@media (min-width: 768px) {
  .header-grid {
    height: 3.15rem;
  }
}

@media (min-width: 1024px) {
  .header-grid {
    height: 3.5rem;
  }
}

/* ===== HEADER LEFT SIDE ===== */
.header-left {
  display: flex;
  align-items: center;
  margin: 0;
  padding: 0;
}

.header-logo {
  font-size: 0.75rem;
  font-weight: bold;
  color: white;
  text-decoration: none;
  white-space: nowrap;
  transition: color 0.2s ease-in-out;
}

.header-logo:hover {
  color: #93c5fd;
}

@media (min-width: 320px) {
  .header-logo {
    font-size: 0.875rem;
  }
}

@media (min-width: 640px) {
  .header-logo {
    font-size: 1.125rem;
  }
}

@media (min-width: 768px) {
  .header-logo {
    font-size: 1.25rem;
  }
}

@media (min-width: 1024px) {
  .header-logo {
    font-size: 1.05rem;
  }
}

@media (min-width: 1280px) {
  .header-logo {
    font-size: 1.3125rem;
  }
}

/* ===== HEADER RIGHT SIDE ===== */
.header-right {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  margin: 0;
  padding: 0;
}

.header-subtitle {
  font-size: 0.875rem;
  font-weight: 500;
  color: white;
  text-align: right;
  line-height: 1.25;
  white-space: nowrap;
}

/* Mobile text - show on small screens */
.header-mobile-text {
  display: inline !important;
}

.header-desktop-text {
  display: none !important;
}

/* Desktop text - show on larger screens */
@media (min-width:720px) {
  .header-mobile-text {
    display: none !important;
  }
  
  .header-desktop-text {
    display: inline !important;
  }
}

@media (min-width: 320px) {
  .header-subtitle {
    font-size: 1rem;
  }
}

@media (min-width: 640px) {
  .header-subtitle {
    font-size: 1.125rem;
  }
}

@media (min-width: 768px) {
  .header-subtitle {
    font-size: 1.25rem;
  }
}

@media (min-width: 1024px) {
  .header-subtitle {
    font-size: 1.05rem;
  }
}

@media (min-width: 1280px) {
  .header-subtitle {
    font-size: 1.3125rem;
  }
}

/* Handle very small screens with text truncation */
@media (max-width: 480px) {
  nav .flex {
    gap: 0.25rem;
  }
  
  nav span {
    font-size: 0.625rem !important;
    line-height: 1rem !important;
  }
}

/* Ensure right text is visible */
nav span {
  color: white !important;
  display: block !important;
  visibility: visible !important;
  opacity: 1 !important;
}

/* Ensure proper text wrapping and overflow handling */
.responsive-text {
  word-wrap: break-word;
  overflow-wrap: break-word;
  hyphens: auto;
}

/* Handle very small screens with horizontal scrolling prevention */
@media (max-width: 320px) {
  .container {
    min-width: 320px;
  }
}

/* Ultra-wide screen optimizations */
@media (min-width: 2560px) {
  .container {
    max-width: 90vw;
    margin: 0 auto;
  }
}

/* High DPI display optimizations */
@media (-webkit-min-device-pixel-ratio: 2), (min-resolution: 192dpi) {
  .text {
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }
}

/* Landscape mobile optimizations */
@media (orientation: landscape) and (max-height: 500px) {
  .nav-height {
    height: 3rem;
  }
}

/* Portrait mobile optimizations */
@media (orientation: portrait) and (max-width: 480px) {
  .nav-height {
    height: 3.5rem;
  }
}

/* Ensure proper touch targets on mobile */
@media (max-width: 768px) {
  .touch-target {
    min-height: 44px;
    min-width: 44px;
  }
}

/* Smooth transitions for responsive changes */
* {
  transition: font-size 0.2s ease-in-out, padding 0.2s ease-in-out, margin 0.2s ease-in-out;
}

/* Prevent horizontal scroll on all devices */
html, body {
  overflow-x: hidden;
  max-width: 100vw;
}

/* Container queries support (when available) */
@container (min-width: 320px) {
  .responsive-content {
    font-size: 0.75rem;
  }
}

@container (min-width: 640px) {
  .responsive-content {
    font-size: 0.875rem;
  }
}

@container (min-width: 1024px) {
  .responsive-content {
    font-size: 1rem;
  }
}

/* Print styles */
@media print {
  .no-print {
    display: none !important;
  }
  
  .print-friendly {
    color: black !important;
    background: white !important;
  }
}

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}

/* High contrast mode support */
@media (prefers-contrast: high) {
  .high-contrast {
    border: 2px solid;
  }
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
  .dark-mode {
    background-color: #1a1a1a;
    color: #ffffff;
  }
}

/* ===== MAIN CONTENT LAYOUT ===== */
.main-content {
  flex: 1;
  width: 100%;
  padding: 0;
  overflow: hidden;
  box-sizing: border-box;
  position: relative;
}

/* ===== LANDSCAPE MESSAGE (Desktop/Landscape) ===== */
.landscape-message {
  display: none;
  align-items: center;
  justify-content: center;
  height: 100%;
  width: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  text-align: center;
  padding: 2rem;
  box-sizing: border-box;
}

.landscape-content {
  max-width: 400px;
}

.phone-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
  animation: rotate 2s ease-in-out infinite;
}

.portrait-content h2 {
  font-size: 2rem;
  margin: 0 0 1rem 0;
  font-weight: bold;
}

.portrait-content p {
  font-size: 1.1rem;
  margin: 0 0 2rem 0;
  line-height: 1.5;
  opacity: 0.9;
}

.rotation-hint {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.arrow {
  font-size: 2rem;
  animation: bounce 1s ease-in-out infinite;
}

.rotation-hint span {
  font-size: 1rem;
  opacity: 0.8;
}

/* ===== SIMULATION LAYOUT (Portrait Only) ===== */
.simulation-layout {
  display: block;
  height: 100%;
  width: 100%;
}

.content-grid {
  display: grid;
  grid-template-columns: 20% 60% 20%;
  gap: 0.25rem;
  height: 100%;
  width: 100%;
  padding: 0.25rem;
  box-sizing: border-box;
}

/* Portrait layout for mobile, tablets, and iPad Pro */
@media (orientation: portrait) and (max-width: 1366px) {
  .content-grid {
    display: grid;
    grid-template-columns: 1fr;
    grid-template-rows: 40% 30% 30%;
    gap: 0.25rem;
    height: 100%;
    width: 100%;
    padding: 0.25rem;
    box-sizing: border-box;
  }
  
  /* Reorder sections for portrait */
  .analysis-section {
    order: 2;
  }
  
  .map-section {
    order: 1;
  }
  
  .results-section {
    order: 3;
  }
}

/* ===== RESPONSIVE BEHAVIOR ===== */
/* Desktop/Laptop - Always show simulation regardless of orientation */
@media (min-width: 1024px) {
  .landscape-message {
    display: none;
  }
  
  .simulation-layout {
    display: block;
  }
}

/* Landscape-only overlay - hide in portrait mode */
.landscape-only {
  display: none;
}

@media (min-width: 640px) and (orientation: landscape) {
  .landscape-only {
    display: block;
  }
}

/* Desktop always shows landscape overlay regardless of orientation */
@media (min-width: 1024px) {
  .landscape-only {
    display: block;
  }
}


/* Mobile and Tablets - Portrait only simulation */
/* Show simulation layout on mobile and portrait tablets */
@media (max-width: 1023px) and (orientation: portrait) {
  .landscape-message {
    display: none;
  }
  
  .simulation-layout {
    display: block;
  }
}

/* Show landscape message on mobile and tablets in landscape */
@media (max-width: 1023px) and (orientation: landscape) {
  .landscape-message {
    display: flex;
  }
  
  .simulation-layout {
    display: none;
  }
}

/* ===== ANIMATIONS ===== */
@keyframes rotate {
  0%, 100% { transform: rotate(0deg); }
  50% { transform: rotate(90deg); }
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

/* ===== ANALYSIS SECTION (20%) ===== */
.analysis-section {
  background-color: #f3f4f6;
  border: 1px solid #e5e7eb;
  border-radius: 0.25rem;
  padding: 0.25rem;
  overflow-y: auto;
  box-sizing: border-box;
}

/* ===== MAP SECTION (60%) ===== */
.map-section {
  background-color: #dbeafe;
  border: 1px solid #3b82f6;
  border-radius: 0.25rem;
  padding: 0.25rem;
  overflow: hidden;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}


.map-container {
  position: relative;
  flex: 1;
  background-color: #f1f5f9;
  overflow: hidden;
}

.map-container {
  width: 100%;
  height: 100%;
  background: #f1f5f9;
}


/* Map elements - Exact CSS from original DemoPage */
.road-path {
  pointer-events: stroke;
  transition: all 0.2s ease;
}

/* Ensure touch events work on mobile and tablets */
@media (max-width: 1366px) {
  .road-path,
  path[data-road-name],
  line[data-road-name] {
    pointer-events: all;
    touch-action: manipulation;
  }
}

/* Force vertical stacking in portrait mode */
@media (orientation: portrait) {
  .absolute.top-2.right-2 > div {
    flex-direction: column !important;
    align-items: stretch !important;
  }
}

/* Responsive button sizing for different screen sizes */
@media (max-width: 480px) {
  .absolute.top-2.right-2 {
    top: 0.25rem;
    right: 0.25rem;
  }
  
  .absolute.top-2.right-2 button {
    padding: 0.25rem 0.5rem;
    font-size: 0.625rem;
    border-radius: 0.25rem;
  }
}

@media (max-width: 320px) {
  .absolute.top-2.right-2 {
    top: 0.125rem;
    right: 0.125rem;
  }
  
  .absolute.top-2.right-2 button {
    padding: 0.125rem 0.25rem;
    font-size: 0.5rem;
    border-radius: 0.125rem;
  }
}

.road-path.clickable {
  cursor: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 32 32"><defs><filter id="shadow" x="-50%" y="-50%" width="200%" height="200%"><feDropShadow dx="1" dy="1" stdDeviation="1" flood-color="%23000000" flood-opacity="0.3"/></filter></defs><g filter="url(%23shadow)"><circle cx="16" cy="16" r="14" fill="%23ffffff" stroke="%23374151" stroke-width="2"/><path d="M6 14h20c1.1 0 2 .9 2 2v4c0 1.1-.9 2-2 2H6c-1.1 0-2-.9-2-2v-4c0-1.1.9-2 2-2z" fill="%23dc2626"/><path d="M8 10h16v4H8z" fill="%23fbbf24"/><path d="M10 8h12v2H10z" fill="%23f59e0b"/><circle cx="9" cy="20" r="2.5" fill="%231f2937"/><circle cx="23" cy="20" r="2.5" fill="%231f2937"/><circle cx="9" cy="20" r="1" fill="%236b7280"/><circle cx="23" cy="20" r="1" fill="%236b7280"/><path d="M12 12h8v2h-8z" fill="%23ffffff"/></g></svg>') 11 11, pointer;
}

.road-path:hover {
  stroke: #00bfff !important;
  stroke-width: 50 !important;
}

/* Invisible clickable areas - only for easier clicking, no visual effects */
.road-path[stroke="transparent"] {
  pointer-events: stroke;
  cursor: inherit;
}

.road-path[stroke="transparent"]:hover {
  stroke: transparent !important;
  stroke-width: 60 !important;
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

.start-marker,
.dest-marker {
  cursor: pointer;
  transition: r 0.2s ease;
  filter: drop-shadow(0 4px 6px rgba(0, 0, 0, 0.1));
}

.start-marker:hover,
.dest-marker:hover {
  r: 15;
}

.marker-text {
  pointer-events: none;
  user-select: none;
}

.route-path {
  stroke-dasharray: 5,5;
  animation: dash 1s linear infinite;
  stroke-linecap: round;
  stroke-linejoin: round;
}

@keyframes dash {
  to {
    stroke-dashoffset: -10;
  }
}

.vehicle-marker {
  cursor: pointer;
  transition: r 0.2s ease;
  opacity: 0.8;
}

.vehicle-marker:hover {
  r: 45;
}

/* Road tooltip animation */
.road-tooltip {
  animation: fadeIn 0.2s ease-in-out;
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

/* Legend animation */
.animate-fade-in {
  animation: fadeIn 0.3s ease-in-out;
}

/* Hide scrollbar for webkit browsers */
.hide-scrollbar::-webkit-scrollbar {
  display: none;
}

/* Performance optimizations for journey cards */
.will-change-transform {
  will-change: transform;
}

/* Smooth scrolling for journey results */
.scroll-smooth {
  scroll-behavior: smooth;
}

/* Optimize hover effects */
.hover\:bg-slate-750:hover {
  background-color: rgb(51 65 85 / 0.8);
}

/* Better focus states for accessibility */
button:focus {
  outline: 2px solid rgb(59 130 246);
  outline-offset: 2px;
}

/* Legend animations */
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

.animate-fade-in {
  animation: fadeIn 0.3s ease-in-out;
}

/* ===== RESULTS SECTION (20%) ===== */
.results-section {
  background-color: #f0fdf4;
  border: 1px solid #22c55e;
  border-radius: 0.25rem;
  padding: 0.25rem;
  overflow-y: auto;
  box-sizing: border-box;
}

/* ===== SECTION PLACEHOLDERS ===== */
.section-placeholder {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  color: #374151;
}

.section-placeholder h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1.25rem;
  font-weight: bold;
}

.section-placeholder p {
  margin: 0;
  font-size: 0.875rem;
  color: #6b7280;
}
</style>
