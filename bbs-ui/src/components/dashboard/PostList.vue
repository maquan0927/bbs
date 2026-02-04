<template>
  <div>
    <el-row type="flex" justify="center">
      <el-col :span="23">
        <el-button type="primary" size="small" @click="showCreatePostDialog">发帖</el-button>
      </el-col>
    </el-row>

    <el-row type="flex" justify="center">
      <el-col :span="23">
        <el-table :data="data" stripe style="width: 100%" empty-text="暂时无人发帖">
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
              <el-button type="primary" size="small" @click="goToDetail(scope.row.id)">查看</el-button>
              <el-button
                type="danger"
                size="small"
                v-if="canDeletePost(scope.row)"
                @click="deletePost(scope.row.id)">
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-col>
    </el-row>

    <el-row type="flex" justify="center" style="margin-top: 20px;">
      <el-pagination
        @current-change="handleCurrentChange"
        :current-page.sync="currentPage"
        :page-size="pageSize"
        layout="prev, pager, next, jumper"
        :total="total">
      </el-pagination>
    </el-row>

    <el-dialog title="发帖" :visible.sync="createPostDialog">
      <el-form :model="form" ref="form" :rules="formRules">
        <el-form-item label="标题" label-width="80" prop="title">
          <el-input v-model="form.title" style="width: 80%;" placeholder="请输入标题"></el-input>
        </el-form-item>
        <el-form-item label="板块" label-width="80" prop="module">
          <el-select v-model="form.module" placeholder="请选择板块" style="width: 80%;">
            <el-option
              v-for="item in moduleOptions"
              :key="item.id"
              :value="item.id"
              :label="item.name">
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="内容" label-width="80" prop="content">
          <el-input type="textarea" v-model="form.content" style="width: 80%;" placeholder="请输入内容"></el-input>
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="createPostDialog = false">取 消</el-button>
        <el-button type="primary" @click="createPost">确 定</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
// 分页配置
const PAGE_SIZE = 10

export default {
  name: 'PostList',
  props: {
    // 板块ID，如果为空则显示所有板块帖子
    moduleId: {
      type: [String, Number],
      default: null
    }
  },
  data() {
    return {
      data: [],
      currentPage: 1,
      total: 0,
      pageSize: PAGE_SIZE,
      createPostDialog: false,
      moduleOptions: [],
      form: {
        title: null,
        content: null,
        module: null,
      },
      formRules: {
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
    this.loadData()
    this.loadModule()
  },
  watch: {
    // 监听moduleId变化，重新加载数据
    moduleId: {
      handler() {
        this.currentPage = 1
        this.loadData()
      },
      immediate: false
    }
  },
  methods: {
    /**
     * 判断当前用户是否有权限删除帖子
     * @param {Object} post - 帖子对象
     * @returns {Boolean}
     */
    canDeletePost(post) {
      const { user_info } = this
      if (!user_info || !user_info.id) return false

      // 超级管理员可删除
      if (user_info.is_superuser) return true

      // 板块管理员可删除
      if (post.module_detail &&
          post.module_detail.admin &&
          post.module_detail.admin.includes(user_info.id)) {
        return true
      }

      // 发帖人可删除
      if (post.user_detail && post.user_detail.id === user_info.id) {
        return true
      }

      return false
    },

    /**
     * 跳转到帖子详情页
     * @param {Number} id - 帖子ID
     */
    goToDetail(id) {
      this.$router.push('/ui/post/' + id)
    },

    /**
     * 删除帖子
     * @param {Number} id - 帖子ID
     */
    deletePost(id) {
      this.$confirm('是否确认删除该帖?', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        this.axios.delete('/api/post/' + id + '/')
          .then(res => {
            if (res.status === 204) {
              this.$message.success('删除成功')
              this.loadData()
            }
          })
          .catch(err => {
            this.$message.error('删除失败，请稍后重试')
            console.error('删除帖子失败:', err)
          })
      }).catch(() => {
        // 用户取消删除
      })
    },

    /**
     * 显示发帖弹窗
     */
    showCreatePostDialog() {
      const isLogin = this.check_login()
      if (isLogin) {
        this.createPostDialog = true
        // 如果有指定板块，默认选中
        if (this.moduleId) {
          this.form.module = Number(this.moduleId)
        }
      }
    },

    /**
     * 创建帖子
     */
    createPost() {
      this.$refs['form'].validate((valid) => {
        if (valid) {
          this.form.user = this.user_info.id
          this.axios.post('/api/post/', this.form)
            .then(res => {
              if (res.status === 201) {
                this.$message.success('创建成功')
              }
              this.createPostDialog = false
              this.resetForm()
              this.loadData()
            })
            .catch(err => {
              this.$message.error('创建失败，请稍后重试')
              console.error('创建帖子失败:', err)
            })
        }
      })
    },

    /**
     * 重置表单
     */
    resetForm() {
      this.form = {
        title: null,
        content: null,
        module: this.moduleId ? Number(this.moduleId) : null,
      }
      if (this.$refs['form']) {
        this.$refs['form'].resetFields()
      }
    },

    /**
     * 加载板块列表
     */
    loadModule() {
      // 优先使用Vuex中的数据
      if (this.$store.state.module && this.$store.state.module.length > 0) {
        this.moduleOptions = this.$store.state.module
        return
      }

      this.axios.get('/api/module/')
        .then(res => {
          this.moduleOptions = res.data
        })
        .catch(err => {
          console.error('加载板块列表失败:', err)
        })
    },

    /**
     * 加载帖子数据
     */
    loadData() {
      let url = '/api/post/'
      // 如果指定了板块ID，则按板块筛选
      if (this.moduleId) {
        url = '/api/post/?module=' + this.moduleId
      }

      this.axios.get(url, { params: { page: this.currentPage } })
        .then(res => {
          this.data = res.data.results
          this.total = res.data.count
        })
        .catch(err => {
          this.$message.error('加载数据失败，请稍后重试')
          console.error('加载帖子数据失败:', err)
        })
    },

    /**
     * 分页切换
     */
    handleCurrentChange() {
      this.loadData()
    },
  },
  computed: {
    user_info() {
      return this.$store.state.user_info
    }
  }
}
</script>
