<template>
  <div class="not-found">
    <h1>404</h1>
    <p>Page not found</p>
    <router-link to="/" class="btn-home">← Back to comments</router-link>
  </div>
</template>

<style scoped>
.not-found {
  text-align: center;
  padding: 60px 20px;
}
h1 {
  font-size: 72px;
  color: #1a73e8;
  margin-bottom: 8px;
}
p {
  font-size: 18px;
  color: #666;
  margin-bottom: 24px;
}
.btn-home {
  display: inline-block;
  background: #1a73e8;
  color: #fff;
  padding: 10px 24px;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
}
.btn-home:hover {
  background: #1557b0;
  text-decoration: none;
}
</style>
