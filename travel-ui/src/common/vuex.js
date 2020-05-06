import Vue from 'vue'
import Vuex from 'vuex'
Vue.use(Vuex)

export default new Vuex.Store({
  state: {
    // 页面高度
    clientHeight: 600,
    clientWidth: 1200,
    // 当前用户的权限信息
    user_info: {
      "id":0,
      "username":"",
    },
  },
  mutations: {
    set_client_height(state, height){
      state.clientHeight = height
    },
    set_client_width(state, width){
      state.clientWidth = width
    },
    set_user_info(state, new_user){
      state.user_info = new_user
    },
  }
})
