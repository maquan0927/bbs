<template>
  <PostList :moduleId="$route.params.id" />
</template>

<script>
import PostList from './PostList.vue'

export default {
  name: 'Module',
  components: {
    PostList
  }
}
</script>
