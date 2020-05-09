<template>
  <div>
    <el-row type="flex" justify="center">
      <el-col :span="23">
        <el-button type="primary" size="small" @click="show_create_post_dialog">发帖</el-button>
      </el-col>
    </el-row>

    <el-row type="flex" justify="center">
      <el-col :span="23">
        <el-table :data="data" stripe style="width: 100%">
          <el-table-column prop="module" label="板块" width="180" align="center">
            <template slot-scope="scope">
              {{ scope.row.module_detail.name }}
            </template>
          </el-table-column>
          <el-table-column prop="title" label="标题" width="180" align="center"></el-table-column>
          <el-table-column prop="content" label="内容" align="center" show-overflow-tooltip></el-table-column>
          <el-table-column prop="user" label="发帖人" width="180" align="center">
            <template slot-scope="scope">
              {{ scope.row.user_detail.username }}
            </template>
          </el-table-column>
          <el-table-column prop="create_time" label="发帖时间" width="180" align="center"></el-table-column>
          <el-table-column label="操作" width="200" align="center">
            <template slot-scope="scope">
              <el-button type="primary" size="small" @click="go_to_detail(scope.row.id)">查看</el-button>
              <el-button type="danger" size="small" v-if="user_info.is_superuser || scope.row.module_detail.admin.includes(user_info.id) || scope.row.user_detail.id == user_info.id" @click="delete_post(scope.row.id)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-col>
    </el-row>

    <el-row type="flex" justify="center" style="margin-top: 20px;">
      <el-pagination @current-change="handleCurrentChange" :current-page.sync="current_page" :page-size="10" layout="prev, pager, next, jumper" :total="total"></el-pagination>
    </el-row>

    <el-dialog title="发帖" :visible.sync="create_post_dialog">
      <el-form :model="form" ref="form" :rules="form_rules">
        <el-form-item label="标题" label-width="80" prop="title">
          <el-input v-model="form.title" style="width: 80%;" placeholder="请输入标题"></el-input>
        </el-form-item>
        <el-form-item label="板块" label-width="80" prop="module">
          <el-select v-model="form.module" placeholder="请选择板块" style="width: 80%;">
            <el-option v-for="(i, index) in module_options" :key="index" :value="i.id" :label="i.name"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="内容" label-width="80" prop="content">
          <el-input type="textarea" v-model="form.content" style="width: 80%;" placeholder="请输入内容"></el-input>
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="create_post_dialog = false">取 消</el-button>
        <el-button type="primary" @click="created_post">确 定</el-button>
      </div>
    </el-dialog>
    
  </div>
</template>

<script>
export default {
  data() {
    return {
      data: [],
      current_page: 1,
      total: 0,
      create_post_dialog: false,
      module_options: [],
      form: {
        title: null,
        content: null,
        module: null,
      },
      form_rules: {
        title: [
          { required: true, message: '请输入标题', trigger: 'blur' },
        ],
        module: [
          { required: true, message: '请选择板块', trigger: 'change' },
        ],
        content: [
          { required: true, message: '请输入内容', trigger: 'blur' },
        ],
      }
    }
  },
  created() {
    this.load_data()
    this.load_module()
  },
  methods: {
    go_to_detail(id){
      this.$router.push('/ui/post/' + id)
    },
    delete_post(id){
      this.$confirm('是否确认删除该帖?', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        this.axios.delete('/api/post/' + id + '/')
        .then(res => {
          if(res.status == 204){
            this.$message.success('删除成功');
            this.load_data()
          }
        })
        
      }).catch(() => {        
      });
    },
    show_create_post_dialog() {
      let is_login = this.check_login()
      if(is_login){
        this.create_post_dialog = true
      }
    },
    created_post() {
      this.$refs['form'].validate((valid) => {
        if(valid){
          this.form.user = this.user_info.id
          this.axios.post('/api/post/', this.form)
          .then(res => {
            if(res.status == 201){
              this.$message.success('创建成功');
            }
            this.create_post_dialog = false
            this.load_data()
          })
        }
      })
    },
    load_module(){
      const $this = this
      this.axios.get('/api/module/')
      .then(res => {
        this.module_options = res.data
      })
    },
    load_data() {
      const $this = this
      let url = '/api/post/'
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