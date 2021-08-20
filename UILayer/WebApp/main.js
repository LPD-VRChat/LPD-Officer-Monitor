//import Vue from './vue.js'
import Vue from 'https://cdn.jsdelivr.net/npm/vue@latest/dist/vue.esm.browser.min.js'
import About from 'UILayer/WebApp/components/about.js'

import Navbar from 'UILayer/WebApp/components/navbar.js'

import MainTemplate from 'UILayer/WebApp/templates/main-template.js'
console.log("loaded main.js")

new Vue({
    el: '#app', // This should be the same as your <div id=""> from earlier.
    components: {
        'navbar': Navbar,
        'about': About,
    },
    router,
    template: MainTemplate
})

Vue.use(VueRouter)

const router = new VueRouter({
    routes: [{
        path: '/about',
        component: About,
        name: "About Us Page"
    }]
})