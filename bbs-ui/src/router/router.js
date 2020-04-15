import Vue from 'vue'
import Router from 'vue-router'
import index from '@/components/index'
import store from '../common/vuex'

// 登陆
import login from '@/components/login'

Vue.use(Router)

const router =  new Router({
  mode: 'history',
  routes: [
    { path: '/ui', name: 'ui', component: index,
    children: [
    ]},
    { path: '/ui/login', name: "login", component: login }
  ]
})

router.beforeEach((to, from, next) => {
  if(to.path === '/') {
    next('/ui')
  }else {
    next()
  // if(to.path !== '/ui/login' && !Vue.cookie.get('access_token')){
  //   next('/ui/login?next=' + to.path)
  // }else if(to.path == '/ui/login' && Vue.cookie.get('access_token')){
  //   next('/ui')
  // }else if(to.path === '/') {
  //   next('/ui')
  // }else {
  //   next()
  }
})

export default router