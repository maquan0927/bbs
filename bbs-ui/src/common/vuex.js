import Vue from 'vue'
import Vuex from 'vuex'
Vue.use(Vuex)

export default new Vuex.Store({
  state: {
    // 页面高度
    clientHeight: 600,
    clientWidth: 1200,
    // 请求进度中
    processing: false,
    // 当前用户的权限信息
    user_info: {
      "id":0,
      "username":"",
      "birthday": "",
      "sex": "",
      "email": "",
      "is_superuser": false,
    },
    module: []
  },
  mutations: {
    set_client_height(state, height){
      state.clientHeight = height
    },
    set_client_width(state, width){
      state.clientWidth = width
    },
    set_processing(state, process){
      state.processing = process
    },
    set_user_info(state, new_user){
      state.user_info = new_user
    },
    set_module(state, new_module){
      state.module = new_module
    }
  }
})
