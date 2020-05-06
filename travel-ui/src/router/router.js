import Vue from 'vue'
import Router from 'vue-router'
import index from '@/components/index'

Vue.use(Router)

const router =  new Router({
  mode: 'history',
  routes: [
    { path: '/ui', name: 'ui', component: index,
      children: [
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