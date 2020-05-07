import Vue from 'vue'
import VueCookie from 'vue-cookie'
import router from '../router/router.js'
import { MessageBox } from 'element-ui'

Vue.use(VueCookie)

Vue.prototype.check_login = function(url="/ui"){
  /* 
  验证用户是否登陆
  */
  if(Vue.cookie.get('access_token')){
    return true
  }else{
    return false
  }
}