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
          <div class="section-placeholder">
            <h3>Map Section</h3>
            <p>60% width</p>
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
</template>

<script>
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
      
      // Ready for your data properties
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
    
    // Ready for your mounted logic
  },
  beforeUnmount() {
    // Clean up listeners
    window.removeEventListener('resize', this.handleResize)
    window.removeEventListener('orientationchange', this.handleResize)
    document.removeEventListener('visibilitychange', this.updateViewport)
    
    if (this.resizeTimeout) {
      clearTimeout(this.resizeTimeout)
    }
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
