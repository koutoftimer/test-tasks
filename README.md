Overview
========

This is SPA appliction that allows to leave comments and post replies. It
allows to attach small images and text files. Registered users can like/dislike
posts and configure profile (set avatar and homepage URL) on top of that.

Deployed at https://comments.ruslan-kovtun.pp.ua/

[![Watch demo on YouTube](https://img.youtube.com/vi/4cERm6zf4rk/0.jpg)](https://www.youtube.com/watch?v=4cERm6zf4rk)

Quick start
===========

```console
$ git clone --depth=1 <repo> <destination folder>
$ cd <destination folder>
$ echo "127.0.0.1 api.comments dev.comments web.comments" | sudo tee --append /etc/hosts
$ cd ./src/frontend/ && npm i && npm run build && cd -  # or `npm run dev`
$ podman compose -f compose-dev.yaml up --build
$ xdg-open http://web.comments:8002  # or http://dev.comments:5173
```

* `api.comments`, `dev.comments` and `web.comments` are helper domains to
  identify and resolve CORS issues early during development.

* Both frontend and backend for development version are running on port `8002`
  and the only distinction between them is host name.

* For ease of frontend development you can run 
  `cd ./src/frontend/ && npm run dev`, then open http://dev.comments:5173

* Most configuration is done via `.env` file for development and `.env.prod`
  for production.

* You can use `docker` instead of `podman`.

TODO
====

- [x] Use rich text editor: https://vueup.github.io/vue-quill/
- [ ] WS: likes, new posts
