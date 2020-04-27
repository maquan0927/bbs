import Vue from 'vue'
import Router from 'vue-router'
import index from '@/components/index'
import store from '../common/vuex'

// 注册/登陆/找回密码全局样式
import login_template from '@/components/login/login_template'
// 登陆
import login from '@/components/login/login'
// 注册
import register from '@/components/login/register'

// 首页或其他类型帖子
import module_index from '@/components/dashboard/index'
import module from '@/components/dashboard/module'

Vue.use(Router)

const router =  new Router({
  mode: 'history',
  routes: [
    { path: '/ui', name: 'ui', component: index,
      children: [
        { path: '/ui', name: "inidex", component: module_index},
        { path: '/ui/module/:id', name: "module", component: module}
      ]
    },
    { path: '/ui/login', name: 'login_template', component: login_template,
      children: [
        { path: '/ui/login', name: "login", component: login },
        { path: '/ui/register', name: "register", component: register }
      ]
    },
  ]
})

router.beforeEach((to, from, next) => {
  if(to.path === '/') {
    next('/ui')
  }else {
    next()
  }
})

export default router