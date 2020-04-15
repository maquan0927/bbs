import Vue from 'vue'
import VueCookie from 'vue-cookie'
Vue.use(VueCookie)
import router from '../router/router.js'

Vue.prototype.check_login = function(){
  /* 
  验证用户是否登陆
  */
  if(Vue.cookie.get('access_token')){
    return true
  }else{
    router.push('/ui/login')
  }
}