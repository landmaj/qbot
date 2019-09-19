Qbot
----
<img src="https://github.com/landmaj/qbot/workflows/build/badge.svg" width="200" alt="Build Status">

### Installation
For an easy deployment, use Dokku. [Let's Encrypt](https://github.com/dokku/dokku-letsencrypt)
and [Postgres](https://github.com/dokku/dokku-postgres) plugins are required.

```
dokku apps:create qbot
dokku domains:add qbot qbot.w-ski.dev
dokku letsencrypt qbot
```

Configuration is stored in environmental variables. They can be tricky in Dokku, so check
[the documentation](http://dokku.viewdocs.io/dokku/configuration/environment-variables/).
All the required variables are listed in [`.env`](.env) file.

```
dokku config:set qbot VARIABLE=VALUE
```

Create and link Postgres database. The second step will create `DATABASE_URL` environmental
variable available to the Qbot app.

```
export POSTGRES_IMAGE_VERSION="11.4"
dokku postgres:create qbot_db
dokku config:set qbot POSTGRES_DATABASE_SCHEME=postgresql
dokku postgres:link qbot_db qbot
```

Add your public SSH key to authorized keys on dokku account, add git remote
and push your code.

```
git remote add dokku dokku@dokku_server:qbot
git push dokku master
```
