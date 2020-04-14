import Vue from 'vue'
import Router from 'vue-router'
import index from '@/components/index'

Vue.use(Router)
import store from '../common/vuex'

export default new Router({
  mode: 'history',
  routes: [
    { path: '/ui', name: 'ui', component: index,
    children: [

    ]},
  ]
})
