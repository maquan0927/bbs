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
    MessageBox.confirm('该操作需要登陆，是否现在登陆？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
      title: '登陆提示'
    }).then(() => {
      router.push("/ui/login?next=" + url)
    }).catch(() => {
      return false
    });
  }
}