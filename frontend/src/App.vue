<template>
  <div id="app">
    <!-- Navigation - Only show on home page -->
    <nav v-if="$route.path === '/'" class="bg-blue-900 text-white shadow-lg">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16">
          <div class="flex items-center">
            <router-link to="/" class="text-xl font-bold hover:text-blue-200">
              SmartTransportation Lab
            </router-link>
          </div>
          <div class="flex items-center space-x-8">
            <router-link to="/" class="hover:text-blue-200">Home</router-link>
            <a href="/#about" class="hover:text-blue-200">About</a>
            <a href="/#team" class="hover:text-blue-200">Team</a>
            <a href="/#research" class="hover:text-blue-200">Research</a>
            <router-link to="/demo" class="hover:text-blue-200">Live Demo</router-link>
            <a href="/#publications" class="hover:text-blue-200">Publications</a>
            <a href="/#contact" class="hover:text-blue-200">Contact</a>
          </div>
        </div>
      </div>
    </nav>

    <!-- Router View -->
    <router-view></router-view>
  </div>
</template>

<script>
export default {
  name: 'App'
}
</script>
