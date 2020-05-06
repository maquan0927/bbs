<template>
  <!-- 容器 -->
  <el-container>
    
    <!-- 顶部导航 -->
    <el-header>
      <el-menu :default-active="activeIndex" class="el-menu-demo" mode="horizontal">
        <el-menu-item index="ui">首页</el-menu-item>
      </el-menu>
    </el-header>

    <!-- 主要区域 -->
    <el-main :style="{ height: clientHeight - 60 + 'px'}">
      <div style="overflow: scroll; background:#fff; padding: 15px 20px;" :style="{ height: clientHeight - 130 + 'px'}">
        <!-- 走马灯 -->
        <el-row>
          <el-col :span="24">
            <el-carousel :interval="1000" type="card" height="300px">
              <el-carousel-item v-for="(item, index) in index_img" :key="index">
                <img :src="item" alt="" width="100%;">
              </el-carousel-item>
            </el-carousel>
          </el-col>
        </el-row>

        <h3>热门推荐</h3>
        <br>

        <el-row>
          <el-col :span="8" v-for="(item, index) in recommend_data" :key="index" style="text-align: center;">
            <img :src="item.img" alt="" width="98%;" @click="show_drawer('recommend', item.id)">
            <h4 @click="show_drawer('recommend', item.id)"><el-link type="primary">{{ item.title }}</el-link></h4>
          </el-col>
        </el-row>

        <br>
        <h3>导游风采</h3>
        <br>

        <el-row>
          <el-col :span="8" v-for="(item, index) in tourguide_data" :key="index" style="text-align: center;">
            <img :src="item.img" alt="" width="98%;" @click="show_drawer('tourguide', item.id)">
            <h4 @click="show_drawer('tourguide', item.id)"><el-link type="primary">{{ item.title }}</el-link></h4>
          </el-col>
        </el-row>
      </div>
    </el-main>

    <!-- 景点和导游使用的抽屉 -->
    <el-drawer
      :title="drawer_data.title"
      :visible.sync="drawer"
      direction="rtl">
      <img :src="drawer_data.img" alt="" width="100%">
      <div style="width: 90%; margin: 20px auto;">{{ drawer_data.content }}</div>
    </el-drawer>

  </el-container>
</template>

<script>
export default {
  data() {
    return {
      activeIndex: 'ui',
      route_maps: {
        "index": "/ui",
      }, 
      drawer: false,
      drawer_data: {title: '测试', img: "http://img.pconline.com.cn/images/upload/upc/tx/wallpaper/1307/10/c6/23169175_1373445345248.jpg", content: "青年是整个社会力量中最积极、最有生气的力量，国家的希望在青年，民族的未来在青年。\
2019年4月30日，习近平总书记在纪念五四运动100周年大会上发表重要讲话，高度评价五四运动的历史意义，明确提出新时代发扬五四精神的重要要求，深情寄语新时代中国青年要以实现中华民族伟大复兴为己任，不辜负党的期望、人民期待、民族重托，不辜负我们这个伟大时代。"},
      index_img: ["http://d.hiphotos.baidu.com/zhidao/pic/item/6a63f6246b600c334c3e91cb1e4c510fd9f9a16a.jpg", "http://img.pconline.com.cn/images/upload/upc/tx/wallpaper/1307/10/c6/23169175_1373445345248.jpg", "http://pic1.win4000.com/wallpaper/0/543f8b4b0fbc1.jpg", "http://bbsfiles.vivo.com.cn/vivobbs/attachment/forum/201810/19/150133hk0jedj00ejae006.jpg", "http://file.mumayi.com/forum/201401/16/231735cfp4046206r4i705.jpg"],
      recommend_data: [{title: '测试1', img: "http://d.hiphotos.baidu.com/zhidao/pic/item/6a63f6246b600c334c3e91cb1e4c510fd9f9a16a.jpg", id: 1},{title: '测试2', img: "http://img.pconline.com.cn/images/upload/upc/tx/wallpaper/1307/10/c6/23169175_1373445345248.jpg", id: 2},{title: '测试2', img: "http://pic1.win4000.com/wallpaper/0/543f8b4b0fbc1.jpg", id: 3}],
      tourguide_data: [{title: '测试1', img: "http://d.hiphotos.baidu.com/zhidao/pic/item/6a63f6246b600c334c3e91cb1e4c510fd9f9a16a.jpg", id: 1},{title: '测试2', img: "http://img.pconline.com.cn/images/upload/upc/tx/wallpaper/1307/10/c6/23169175_1373445345248.jpg", id: 2},{title: '测试2', img: "http://pic1.win4000.com/wallpaper/0/543f8b4b0fbc1.jpg", id: 3}],
    }
  },
  created(){
  },
  mounted() {
    // 动态设置背景图的高度为浏览器可视区域高度
    // 首先在Virtual DOM渲染数据时，设置下背景图的高度．
    // 测试发现需延时50ms才能设置生效
    setTimeout(_=>{
      this.clientHeight = document.documentElement.clientHeight
    }, 50)
    // 然后监听window的resize事件．在浏览器窗口变化时再设置下背景图高度．
    window.onresize = function () {
      this.clientHeight = document.documentElement.clientHeight
    }
  },
  methods: {
    show_drawer(type, id){
      this.drawer = true
    }
  },
  computed: {
    clientHeight: {
      get(){
        return this.$store.state.clientHeight
      },
      set(value){
        this.$store.commit('set_client_height', value)
      }
    },
    user_info: {
      get(){
        return this.$store.state.user_info
      },
      set(value){
        this.$store.commit('set_user_info', value)
      }
    }
  },
}
</script>

<style scoped>
  .el-main {
    background-color: #f9f9f9;
    color: #333;
  }
</style>