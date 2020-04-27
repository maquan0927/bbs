<template>
  <div>
    <el-row type="flex" justify="center">
      <el-col :span="22">
        <el-table :data="data" stripe style="width: 100%" empty-text="暂时无人发帖">
          <el-table-column prop="module" label="板块" width="180" align="center">
            <template slot-scope="scope">
              {{ scope.row.module.name }}
            </template>
          </el-table-column>
          <el-table-column prop="title" label="标题" width="180" align="center"></el-table-column>
          <el-table-column prop="content" label="内容" align="center" show-overflow-tooltip></el-table-column>
          <el-table-column prop="user" label="发帖人" width="180" align="center">
            <template slot-scope="scope">
              {{ scope.row.user.username }}
            </template>
          </el-table-column>
          <el-table-column prop="create_time" label="发帖时间" width="180" align="center"></el-table-column>
        </el-table>
      </el-col>
    </el-row>

    <el-row type="flex" justify="center" style="margin-top: 20px;">
      <el-pagination @current-change="handleCurrentChange" :current-page.sync="current_page" :page-size="10" layout="prev, pager, next, jumper" :total="total"></el-pagination>
    </el-row>
    
  </div>
</template>

<script>
export default {
  data() {
    return {
      data: [],
      current_page: 1,
      total: 0
    }
  },
  created() {
    this.load_data()
  },
  methods: {
    load_data() {
      const $this = this
      let url = '/api/post/?module=' + this.$route.params.id
      this.axios.get(url, {params: {page: this.current_page}})
      .then(res => {
        this.data = res.data.results
        this.total = res.data.count
      })
    },
    handleCurrentChange() {
      this.load_data()
    },
  },
  computed: {
    user_info: {
      get(){
        return this.$store.state.user_info
      },
    }
  }
}
</script>