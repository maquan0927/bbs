import Vue from 'vue'
import App from './App.vue'
import store from './common/vuex'
import router from './router/router'
import './common/axios'
import 'element-ui/lib/theme-chalk/index.css'
import ElementUI from 'element-ui'
import "@/assets/iconfont/iconfont.css"; 

Vue.use(ElementUI)

Vue.config.productionTip = false

new Vue({
  el: '#app',
  router,
  template: '<App/>',
  components: { App },
  store
})