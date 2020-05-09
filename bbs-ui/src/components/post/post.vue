<template>
  <div>
    <el-row type="flex" justify="center">
      <el-col :span="22">
        <!-- 帖子 -->
        <h4 style="padding: 10px;">模块：{{ data.module_detail.name }}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;标题：{{ data.title }}</h4>
        <div style="border-top:1px dashed #333;border-bottom:1px dashed #333;margin-top: 20px;min-height: 50px;padding: 10px;overflow:hidden;">
          {{ data.content }}
          <div style="margin-top: 30px;float: right;font-size: 14px;">
            发帖时间：{{ data.create_time }}
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
            发帖人：{{ data.user_detail.username }}
          </div>
        </div>

        <!-- 回帖 -->
        <div v-for="(repost, index) in data.reposts" :key="index" style="border-bottom:1px dashed #333;min-height: 50px;padding: 10px;overflow:hidden;">
          {{ repost.content }}
          <div style="margin-top: 30px;float: right;font-size: 14px;">
            回帖时间：{{ repost.create_time }}
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
            回帖人：{{ repost.user_info }}
          </div>
        </div>

        <!-- 回复 -->
        <h4 style="padding: 10px;margin-top: 20px;">回复</h4>
        <el-form :model="form" :rules="rules" ref="form" label-width="100px">
          <el-form-item label="回帖内容" prop="content">
            <el-input type="textarea" :autosize="{ minRows: 5, maxRows: 10}" v-model="form.content" placeholder="回帖内容" style="width: 70%;"></el-input>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" size="small" @click="submit_repost">回复</el-button>
          </el-form-item>
        </el-form>
      </el-col>
    </el-row>
  </div>
</template>

<script>
export default {
  data() {
    return {
      data: {
        title: null,
        content: null,
        reposts: [],
        user_detail: {
          username: null,
        },
        module_detail: {
          name: null,
        }
      },
      form: {
        content: null,
        post: this.$route.params.id,
      },
      rules: {
        content: [
          { required: true, message: '请输入回帖内容', trigger: 'blur' },
        ],
      }
    }
  },
  created() {
    this.load_data()
  },
  methods: {
    submit_repost() {
      let is_login = this.check_login()
      if(is_login){
        this.axios.post('/api/repost/', this.form)
        .then(res => {
          this.form = {
            content: null,
            post: this.$route.params.id
          }
          this.load_data()
        })
      }
    },
    load_data() {
      const $this = this
      this.axios.get('/api/post/' + this.$route.params.id + '/')
      .then(res => {
        this.data = res.data
      })
    }
  }
}
</script>