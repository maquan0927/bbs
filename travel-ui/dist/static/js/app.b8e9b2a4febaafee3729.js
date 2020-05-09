webpackJsonp([1],{FGLd:function(e,t){},NHnr:function(e,t,o){"use strict";Object.defineProperty(t,"__esModule",{value:!0});var i=o("7+uW"),s={render:function(){var e=this.$createElement,t=this._self._c||e;return t("div",{attrs:{id:"app"}},[t("router-view")],1)},staticRenderFns:[]};var r=o("VU/8")({name:"App"},s,!1,function(e){o("FGLd")},null,null).exports,n=o("NYxO");i.default.use(n.a);var a=new n.a.Store({state:{clientHeight:600,clientWidth:1200,user_info:{id:0,username:""}},mutations:{set_client_height:function(e,t){e.clientHeight=t},set_client_width:function(e,t){e.clientWidth=t},set_user_info:function(e,t){e.user_info=t}}}),l=o("/ocq"),u={data:function(){return{activeIndex:"ui",route_maps:{ui:"/ui"},drawer:!1,login_dialog:!1,register_dialog:!1,message_dialog:!1,register_form:{username:null,password:null},loginform:{user:null,password:null},messageform:{title:null,content:null},drawer_data:{},index_img:[],recomend_data:[],tourguide_data:[],login_rules:{username:[{required:!0,message:"请输入用户名",trigger:"blur"}],password:[{required:!0,message:"请输入密码",trigger:"blur"}]},message_rules:{title:[{required:!0,message:"请输入标题",trigger:"blur"}],content:[{required:!0,message:"请输入内容",trigger:"blur"}]}}},created:function(){this.load_index_img(),this.load_recommend(),this.load_tourguide()},mounted:function(){var e=this;setTimeout(function(t){e.clientHeight=document.documentElement.clientHeight},50),window.onresize=function(){this.clientHeight=document.documentElement.clientHeight}},methods:{register:function(){var e=this;this.$refs.register_form.validate(function(t){if(!t)return!1;e.axios.post("/api/user/",e.register_form).then(function(t){e.$message.success("注册成功"),e.register_dialog=!1,e.login_dialog=!0})})},show_register:function(){this.login_dialog=!1,this.register_dialog=!0},submit_message:function(){var e=this;this.$refs.messageform.validate(function(t){if(!t)return!1;e.axios.post("/api/message/",e.messageform).then(function(t){e.$message.success("留言成功"),e.message_dialog=!1})})},logout:function(){this.$cookie.delete("access_token"),this.$cookie.delete("refresh_token"),this.$cookie.delete("username"),this.$router.go(0)},login:function(){var e=this,t=this;this.$refs.loginform.validate(function(o){if(!o)return!1;var i=new URLSearchParams;i.append("grant_type","password"),i.append("username",e.loginform.username),i.append("password",e.loginform.password),i.append("client_id","l5cLs3BFLXQCQo1Jkm0hFTo66iJGkkQRxgGmuvDu"),i.append("client_secret","TnqjcKs3RZ5Rlh9Dz3csYSy7dk1Yk0YRhN7qgIF04TP9mc1Av5KfRdCtxps1c1s6314sWht5Rg1ojym3ZY4GR4J8zWqIBfwMIvS1n700PtFOIEwZDELVxbpVTmTgxi2x"),e.axios.post("/oauth/token/",i,{headers:{"Content-Type":"application/x-www-form-urlencoded"},timeout:1e4}).then(function(o){if(200===o.status){t.$message.success("登陆成功");var i=o.data.expires_in+"s";t.$cookie.set("access_token",o.data.access_token,{expires:i}),t.$cookie.set("refresh_token",o.data.refresh_token,{expires:i}),t.$cookie.set("token_type",o.data.token_type,{expires:i}),e.login_dialog=!1,e.message_dialog=!0}else t.$message({message:"登录失败！请检查您的用户名密码",type:"error"})}).catch(function(e){console.log(e),t.$message({message:"登录失败！请检查您的用户名密码",type:"error"}),t.$cookie.delete("access_token"),t.$cookie.delete("refresh_token"),t.$cookie.delete("username")})})},handleSelect:function(e,t){"message"===e?this.check_login()?this.message_dialog=!0:this.login_dialog=!0:"logout"===e&&this.logout()},show_drawer:function(e,t){this.drawer=!0,this.drawer_data=t},load_index_img:function(){var e=this;this.axios.get("/api/index/").then(function(t){e.index_img=t.data})},load_recommend:function(){var e=this;this.axios.get("/api/recomend/").then(function(t){e.recomend_data=t.data})},load_tourguide:function(){var e=this;this.axios.get("/api/tourguide/").then(function(t){e.tourguide_data=t.data})}},computed:{clientHeight:{get:function(){return this.$store.state.clientHeight},set:function(e){this.$store.commit("set_client_height",e)}},user_info:{get:function(){return this.$store.state.user_info},set:function(e){this.$store.commit("set_user_info",e)}}}},c={render:function(){var e=this,t=e.$createElement,o=e._self._c||t;return o("el-container",[o("el-header",[o("el-menu",{staticClass:"el-menu-demo",attrs:{"default-active":e.activeIndex,mode:"horizontal"},on:{select:e.handleSelect}},[o("el-menu-item",{attrs:{index:"ui"}},[e._v("首页")]),e._v(" "),o("el-menu-item",{attrs:{index:"message"}},[e._v("留言")]),e._v(" "),e.$cookie.get("access_token")?o("el-menu-item",{attrs:{index:"logout"}},[e._v("退出登陆")]):e._e()],1)],1),e._v(" "),o("el-main",{style:{height:e.clientHeight-60+"px"}},[o("div",{staticStyle:{overflow:"scroll",background:"#fff",padding:"15px 20px"},style:{height:e.clientHeight-130+"px"}},[o("br"),e._v(" "),o("h3",[e._v("风景轮播")]),e._v(" "),o("br"),e._v(" "),o("el-row",[o("el-col",{attrs:{span:24}},[o("el-carousel",{attrs:{interval:1e3,type:"card",height:"300px"}},e._l(e.index_img,function(e,t){return o("el-carousel-item",{key:t},[o("img",{attrs:{src:e.img,alt:"",width:"100%;"}})])}),1)],1)],1),e._v(" "),o("h3",[e._v("热门推荐")]),e._v(" "),o("br"),e._v(" "),o("el-row",e._l(e.recomend_data,function(t,i){return o("el-col",{key:i,staticStyle:{"text-align":"center"},attrs:{span:8}},[o("img",{attrs:{src:t.img,alt:"",width:"98%",height:"250px"},on:{click:function(o){return e.show_drawer("recomend",t)}}}),e._v(" "),o("h4",{on:{click:function(o){return e.show_drawer("recomend",t)}}},[o("el-link",{attrs:{type:"primary"}},[e._v(e._s(t.title))])],1)])}),1),e._v(" "),o("br"),e._v(" "),o("h3",[e._v("导游风采")]),e._v(" "),o("br"),e._v(" "),o("el-row",e._l(e.tourguide_data,function(t,i){return o("el-col",{key:i,staticStyle:{"text-align":"center"},attrs:{span:8}},[o("img",{attrs:{src:t.img,alt:"",width:"98%",height:"250px"},on:{click:function(o){return e.show_drawer("tourguide",t)}}}),e._v(" "),o("h4",{on:{click:function(o){return e.show_drawer("tourguide",t)}}},[o("el-link",{attrs:{type:"primary"}},[e._v(e._s(t.title))])],1)])}),1)],1)]),e._v(" "),o("el-dialog",{attrs:{title:e.drawer_data.title,visible:e.drawer},on:{"update:visible":function(t){e.drawer=t}}},[o("img",{attrs:{src:e.drawer_data.img,alt:"",width:"100%"}}),e._v(" "),o("div",{staticStyle:{width:"90%",margin:"20px auto"}},[e._v(e._s(e.drawer_data.content))])]),e._v(" "),o("el-dialog",{attrs:{width:"50%",title:"登陆",visible:e.login_dialog},on:{"update:visible":function(t){e.login_dialog=t}}},[o("el-form",{ref:"loginform",attrs:{model:e.loginform,rules:e.login_rules}},[o("el-form-item",{attrs:{label:"用户名","label-width":"100px",prop:"username"}},[o("el-input",{staticStyle:{width:"70%"},attrs:{autocomplete:"off"},model:{value:e.loginform.username,callback:function(t){e.$set(e.loginform,"username",t)},expression:"loginform.username"}})],1),e._v(" "),o("el-form-item",{attrs:{label:"密码","label-width":"100px",prop:"password"}},[o("el-input",{staticStyle:{width:"70%"},attrs:{autocomplete:"off","show-password":""},model:{value:e.loginform.password,callback:function(t){e.$set(e.loginform,"password",t)},expression:"loginform.password"}})],1)],1),e._v(" "),o("div",{staticClass:"dialog-footer",attrs:{slot:"footer"},slot:"footer"},[o("el-button",{attrs:{type:"primary"},on:{click:e.show_register}},[e._v("注 册")]),e._v(" "),o("el-button",{on:{click:function(t){e.login_dialog=!1}}},[e._v("取 消")]),e._v(" "),o("el-button",{attrs:{type:"primary"},on:{click:e.login}},[e._v("确 定")])],1)],1),e._v(" "),o("el-dialog",{attrs:{width:"50%",title:"留言",visible:e.message_dialog},on:{"update:visible":function(t){e.message_dialog=t}}},[o("el-form",{ref:"messageform",attrs:{model:e.messageform,rules:e.message_rules}},[o("el-form-item",{attrs:{label:"标题","label-width":"100px",prop:"title"}},[o("el-input",{staticStyle:{width:"70%"},attrs:{autocomplete:"off"},model:{value:e.messageform.title,callback:function(t){e.$set(e.messageform,"title",t)},expression:"messageform.title"}})],1),e._v(" "),o("el-form-item",{attrs:{label:"内容","label-width":"100px",prop:"content"}},[o("el-input",{staticStyle:{width:"70%"},attrs:{type:"textarea",autosize:{minRows:5,maxRows:10},autocomplete:"off"},model:{value:e.messageform.content,callback:function(t){e.$set(e.messageform,"content",t)},expression:"messageform.content"}})],1)],1),e._v(" "),o("div",{staticClass:"dialog-footer",attrs:{slot:"footer"},slot:"footer"},[o("el-button",{on:{click:function(t){e.message_dialog=!1}}},[e._v("取 消")]),e._v(" "),o("el-button",{attrs:{type:"primary"},on:{click:e.submit_message}},[e._v("确 定")])],1)],1),e._v(" "),o("el-dialog",{attrs:{width:"50%",title:"注册",visible:e.register_dialog},on:{"update:visible":function(t){e.register_dialog=t}}},[o("el-form",{ref:"register_form",attrs:{model:e.register_form,rules:e.login_rules}},[o("el-form-item",{attrs:{label:"用户名","label-width":"100px",prop:"username"}},[o("el-input",{staticStyle:{width:"70%"},attrs:{autocomplete:"off"},model:{value:e.register_form.username,callback:function(t){e.$set(e.register_form,"username",t)},expression:"register_form.username"}})],1),e._v(" "),o("el-form-item",{attrs:{label:"密码","label-width":"100px",prop:"password"}},[o("el-input",{staticStyle:{width:"70%"},attrs:{autocomplete:"off","show-password":""},model:{value:e.register_form.password,callback:function(t){e.$set(e.register_form,"password",t)},expression:"register_form.password"}})],1)],1),e._v(" "),o("div",{staticClass:"dialog-footer",attrs:{slot:"footer"},slot:"footer"},[o("el-button",{on:{click:function(t){e.register_dialog=!1}}},[e._v("取 消")]),e._v(" "),o("el-button",{attrs:{type:"primary"},on:{click:e.register}},[e._v("注 册")])],1)],1)],1)},staticRenderFns:[]};var d=o("VU/8")(u,c,!1,function(e){o("e5dP")},"data-v-9b5b64ea",null).exports;i.default.use(l.a);var m=new l.a({mode:"history",routes:[{path:"/ui",name:"ui",component:d,children:[]}]});m.beforeEach(function(e,t,o){"/"===e.path?o("/ui"):o()});var g=m,f=o("//Fk"),_=o.n(f),p=o("mtWM"),h=o.n(p),v=o("K/Lq"),w=o.n(v),k=o("zL8q"),x=o.n(k);i.default.use(w.a),h.a.defaults.baseURL=Object({NODE_ENV:"production"}).API_ENDPOINT,h.a.interceptors.request.use(function(e){var t=i.default.cookie.get("access_token"),o=i.default.cookie.get("token_type");return t&&o&&(e.headers.Authorization=o+" "+t),e},function(e){return _.a.reject(e)}),h.a.interceptors.response.use(function(e){return e},function(e){return k.Notification.error({title:"请求发生异常！状态码："+e.response.status,message:e.response.statusText}),_.a.resolve(e.response)}),i.default.prototype.axios=h.a;h.a,o("tvR6"),o("muQq");i.default.use(w.a),i.default.prototype.check_login=function(){arguments.length>0&&void 0!==arguments[0]&&arguments[0];return!!i.default.cookie.get("access_token")},i.default.use(x.a),i.default.config.productionTip=!1,new i.default({el:"#app",router:g,template:"<App/>",components:{App:r},store:a})},e5dP:function(e,t){},muQq:function(e,t){},tvR6:function(e,t){}},["NHnr"]);
//# sourceMappingURL=app.b8e9b2a4febaafee3729.js.map