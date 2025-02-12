/* eslint-disable */

// @ts-nocheck

// noinspection JSUnusedGlobalSymbols

// This file was automatically generated by TanStack Router.
// You should NOT make any changes in this file as it will be overwritten.
// Additionally, you should also exclude this file from your linter and/or formatter to prevent it from being checked or modified.

import { createFileRoute } from '@tanstack/react-router'

// Import Routes

import { Route as rootRoute } from './routes/__root'
import { Route as LayoutImport } from './routes/_layout'
import { Route as IndexImport } from './routes/index'
import { Route as LayoutSessionsIndexImport } from './routes/_layout/sessions/index'
import { Route as LayoutSessionsSessionIdImport } from './routes/_layout/sessions/$sessionId'
import { Route as LayoutModelsLayoutModelsImport } from './routes/_layout/models/_layout-models'
import { Route as LayoutDataLayoutDatasourcesImport } from './routes/_layout/data/_layout-datasources'
import { Route as LayoutAnalyticsLayoutModelsImport } from './routes/_layout/analytics/_layout-models'
import { Route as LayoutModelsLayoutModelsIndexImport } from './routes/_layout/models/_layout-models/index'
import { Route as LayoutDataLayoutDatasourcesIndexImport } from './routes/_layout/data/_layout-datasources/index'
import { Route as LayoutAnalyticsLayoutModelsIndexImport } from './routes/_layout/analytics/_layout-models/index'
import { Route as LayoutDataLayoutDatasourcesDataSourceIdImport } from './routes/_layout/data/_layout-datasources/$dataSourceId'

// Create Virtual Routes

const LayoutModelsImport = createFileRoute('/_layout/models')()
const LayoutDataImport = createFileRoute('/_layout/data')()
const LayoutAnalyticsImport = createFileRoute('/_layout/analytics')()

// Create/Update Routes

const LayoutRoute = LayoutImport.update({
  id: '/_layout',
  getParentRoute: () => rootRoute,
} as any).lazy(() => import('./routes/_layout.lazy').then((d) => d.Route))

const IndexRoute = IndexImport.update({
  id: '/',
  path: '/',
  getParentRoute: () => rootRoute,
} as any).lazy(() => import('./routes/index.lazy').then((d) => d.Route))

const LayoutModelsRoute = LayoutModelsImport.update({
  id: '/models',
  path: '/models',
  getParentRoute: () => LayoutRoute,
} as any)

const LayoutDataRoute = LayoutDataImport.update({
  id: '/data',
  path: '/data',
  getParentRoute: () => LayoutRoute,
} as any)

const LayoutAnalyticsRoute = LayoutAnalyticsImport.update({
  id: '/analytics',
  path: '/analytics',
  getParentRoute: () => LayoutRoute,
} as any)

const LayoutSessionsIndexRoute = LayoutSessionsIndexImport.update({
  id: '/sessions/',
  path: '/sessions/',
  getParentRoute: () => LayoutRoute,
} as any).lazy(() =>
  import('./routes/_layout/sessions/index.lazy').then((d) => d.Route),
)

const LayoutSessionsSessionIdRoute = LayoutSessionsSessionIdImport.update({
  id: '/sessions/$sessionId',
  path: '/sessions/$sessionId',
  getParentRoute: () => LayoutRoute,
} as any).lazy(() =>
  import('./routes/_layout/sessions/$sessionId.lazy').then((d) => d.Route),
)

const LayoutModelsLayoutModelsRoute = LayoutModelsLayoutModelsImport.update({
  id: '/_layout-models',
  getParentRoute: () => LayoutModelsRoute,
} as any)

const LayoutDataLayoutDatasourcesRoute =
  LayoutDataLayoutDatasourcesImport.update({
    id: '/_layout-datasources',
    getParentRoute: () => LayoutDataRoute,
  } as any)

const LayoutAnalyticsLayoutModelsRoute =
  LayoutAnalyticsLayoutModelsImport.update({
    id: '/_layout-models',
    getParentRoute: () => LayoutAnalyticsRoute,
  } as any)

const LayoutModelsLayoutModelsIndexRoute =
  LayoutModelsLayoutModelsIndexImport.update({
    id: '/',
    path: '/',
    getParentRoute: () => LayoutModelsLayoutModelsRoute,
  } as any).lazy(() =>
    import('./routes/_layout/models/_layout-models/index.lazy').then(
      (d) => d.Route,
    ),
  )

const LayoutDataLayoutDatasourcesIndexRoute =
  LayoutDataLayoutDatasourcesIndexImport.update({
    id: '/',
    path: '/',
    getParentRoute: () => LayoutDataLayoutDatasourcesRoute,
  } as any).lazy(() =>
    import('./routes/_layout/data/_layout-datasources/index.lazy').then(
      (d) => d.Route,
    ),
  )

const LayoutAnalyticsLayoutModelsIndexRoute =
  LayoutAnalyticsLayoutModelsIndexImport.update({
    id: '/',
    path: '/',
    getParentRoute: () => LayoutAnalyticsLayoutModelsRoute,
  } as any).lazy(() =>
    import('./routes/_layout/analytics/_layout-models/index.lazy').then(
      (d) => d.Route,
    ),
  )

const LayoutDataLayoutDatasourcesDataSourceIdRoute =
  LayoutDataLayoutDatasourcesDataSourceIdImport.update({
    id: '/$dataSourceId',
    path: '/$dataSourceId',
    getParentRoute: () => LayoutDataLayoutDatasourcesRoute,
  } as any).lazy(() =>
    import('./routes/_layout/data/_layout-datasources/$dataSourceId.lazy').then(
      (d) => d.Route,
    ),
  )

// Populate the FileRoutesByPath interface

declare module '@tanstack/react-router' {
  interface FileRoutesByPath {
    '/': {
      id: '/'
      path: '/'
      fullPath: '/'
      preLoaderRoute: typeof IndexImport
      parentRoute: typeof rootRoute
    }
    '/_layout': {
      id: '/_layout'
      path: ''
      fullPath: ''
      preLoaderRoute: typeof LayoutImport
      parentRoute: typeof rootRoute
    }
    '/_layout/analytics': {
      id: '/_layout/analytics'
      path: '/analytics'
      fullPath: '/analytics'
      preLoaderRoute: typeof LayoutAnalyticsImport
      parentRoute: typeof LayoutImport
    }
    '/_layout/analytics/_layout-models': {
      id: '/_layout/analytics/_layout-models'
      path: '/analytics'
      fullPath: '/analytics'
      preLoaderRoute: typeof LayoutAnalyticsLayoutModelsImport
      parentRoute: typeof LayoutAnalyticsRoute
    }
    '/_layout/data': {
      id: '/_layout/data'
      path: '/data'
      fullPath: '/data'
      preLoaderRoute: typeof LayoutDataImport
      parentRoute: typeof LayoutImport
    }
    '/_layout/data/_layout-datasources': {
      id: '/_layout/data/_layout-datasources'
      path: '/data'
      fullPath: '/data'
      preLoaderRoute: typeof LayoutDataLayoutDatasourcesImport
      parentRoute: typeof LayoutDataRoute
    }
    '/_layout/models': {
      id: '/_layout/models'
      path: '/models'
      fullPath: '/models'
      preLoaderRoute: typeof LayoutModelsImport
      parentRoute: typeof LayoutImport
    }
    '/_layout/models/_layout-models': {
      id: '/_layout/models/_layout-models'
      path: '/models'
      fullPath: '/models'
      preLoaderRoute: typeof LayoutModelsLayoutModelsImport
      parentRoute: typeof LayoutModelsRoute
    }
    '/_layout/sessions/$sessionId': {
      id: '/_layout/sessions/$sessionId'
      path: '/sessions/$sessionId'
      fullPath: '/sessions/$sessionId'
      preLoaderRoute: typeof LayoutSessionsSessionIdImport
      parentRoute: typeof LayoutImport
    }
    '/_layout/sessions/': {
      id: '/_layout/sessions/'
      path: '/sessions'
      fullPath: '/sessions'
      preLoaderRoute: typeof LayoutSessionsIndexImport
      parentRoute: typeof LayoutImport
    }
    '/_layout/data/_layout-datasources/$dataSourceId': {
      id: '/_layout/data/_layout-datasources/$dataSourceId'
      path: '/$dataSourceId'
      fullPath: '/data/$dataSourceId'
      preLoaderRoute: typeof LayoutDataLayoutDatasourcesDataSourceIdImport
      parentRoute: typeof LayoutDataLayoutDatasourcesImport
    }
    '/_layout/analytics/_layout-models/': {
      id: '/_layout/analytics/_layout-models/'
      path: '/'
      fullPath: '/analytics/'
      preLoaderRoute: typeof LayoutAnalyticsLayoutModelsIndexImport
      parentRoute: typeof LayoutAnalyticsLayoutModelsImport
    }
    '/_layout/data/_layout-datasources/': {
      id: '/_layout/data/_layout-datasources/'
      path: '/'
      fullPath: '/data/'
      preLoaderRoute: typeof LayoutDataLayoutDatasourcesIndexImport
      parentRoute: typeof LayoutDataLayoutDatasourcesImport
    }
    '/_layout/models/_layout-models/': {
      id: '/_layout/models/_layout-models/'
      path: '/'
      fullPath: '/models/'
      preLoaderRoute: typeof LayoutModelsLayoutModelsIndexImport
      parentRoute: typeof LayoutModelsLayoutModelsImport
    }
  }
}

// Create and export the route tree

interface LayoutAnalyticsLayoutModelsRouteChildren {
  LayoutAnalyticsLayoutModelsIndexRoute: typeof LayoutAnalyticsLayoutModelsIndexRoute
}

const LayoutAnalyticsLayoutModelsRouteChildren: LayoutAnalyticsLayoutModelsRouteChildren =
  {
    LayoutAnalyticsLayoutModelsIndexRoute:
      LayoutAnalyticsLayoutModelsIndexRoute,
  }

const LayoutAnalyticsLayoutModelsRouteWithChildren =
  LayoutAnalyticsLayoutModelsRoute._addFileChildren(
    LayoutAnalyticsLayoutModelsRouteChildren,
  )

interface LayoutAnalyticsRouteChildren {
  LayoutAnalyticsLayoutModelsRoute: typeof LayoutAnalyticsLayoutModelsRouteWithChildren
}

const LayoutAnalyticsRouteChildren: LayoutAnalyticsRouteChildren = {
  LayoutAnalyticsLayoutModelsRoute:
    LayoutAnalyticsLayoutModelsRouteWithChildren,
}

const LayoutAnalyticsRouteWithChildren = LayoutAnalyticsRoute._addFileChildren(
  LayoutAnalyticsRouteChildren,
)

interface LayoutDataLayoutDatasourcesRouteChildren {
  LayoutDataLayoutDatasourcesDataSourceIdRoute: typeof LayoutDataLayoutDatasourcesDataSourceIdRoute
  LayoutDataLayoutDatasourcesIndexRoute: typeof LayoutDataLayoutDatasourcesIndexRoute
}

const LayoutDataLayoutDatasourcesRouteChildren: LayoutDataLayoutDatasourcesRouteChildren =
  {
    LayoutDataLayoutDatasourcesDataSourceIdRoute:
      LayoutDataLayoutDatasourcesDataSourceIdRoute,
    LayoutDataLayoutDatasourcesIndexRoute:
      LayoutDataLayoutDatasourcesIndexRoute,
  }

const LayoutDataLayoutDatasourcesRouteWithChildren =
  LayoutDataLayoutDatasourcesRoute._addFileChildren(
    LayoutDataLayoutDatasourcesRouteChildren,
  )

interface LayoutDataRouteChildren {
  LayoutDataLayoutDatasourcesRoute: typeof LayoutDataLayoutDatasourcesRouteWithChildren
}

const LayoutDataRouteChildren: LayoutDataRouteChildren = {
  LayoutDataLayoutDatasourcesRoute:
    LayoutDataLayoutDatasourcesRouteWithChildren,
}

const LayoutDataRouteWithChildren = LayoutDataRoute._addFileChildren(
  LayoutDataRouteChildren,
)

interface LayoutModelsLayoutModelsRouteChildren {
  LayoutModelsLayoutModelsIndexRoute: typeof LayoutModelsLayoutModelsIndexRoute
}

const LayoutModelsLayoutModelsRouteChildren: LayoutModelsLayoutModelsRouteChildren =
  {
    LayoutModelsLayoutModelsIndexRoute: LayoutModelsLayoutModelsIndexRoute,
  }

const LayoutModelsLayoutModelsRouteWithChildren =
  LayoutModelsLayoutModelsRoute._addFileChildren(
    LayoutModelsLayoutModelsRouteChildren,
  )

interface LayoutModelsRouteChildren {
  LayoutModelsLayoutModelsRoute: typeof LayoutModelsLayoutModelsRouteWithChildren
}

const LayoutModelsRouteChildren: LayoutModelsRouteChildren = {
  LayoutModelsLayoutModelsRoute: LayoutModelsLayoutModelsRouteWithChildren,
}

const LayoutModelsRouteWithChildren = LayoutModelsRoute._addFileChildren(
  LayoutModelsRouteChildren,
)

interface LayoutRouteChildren {
  LayoutAnalyticsRoute: typeof LayoutAnalyticsRouteWithChildren
  LayoutDataRoute: typeof LayoutDataRouteWithChildren
  LayoutModelsRoute: typeof LayoutModelsRouteWithChildren
  LayoutSessionsSessionIdRoute: typeof LayoutSessionsSessionIdRoute
  LayoutSessionsIndexRoute: typeof LayoutSessionsIndexRoute
}

const LayoutRouteChildren: LayoutRouteChildren = {
  LayoutAnalyticsRoute: LayoutAnalyticsRouteWithChildren,
  LayoutDataRoute: LayoutDataRouteWithChildren,
  LayoutModelsRoute: LayoutModelsRouteWithChildren,
  LayoutSessionsSessionIdRoute: LayoutSessionsSessionIdRoute,
  LayoutSessionsIndexRoute: LayoutSessionsIndexRoute,
}

const LayoutRouteWithChildren =
  LayoutRoute._addFileChildren(LayoutRouteChildren)

export interface FileRoutesByFullPath {
  '/': typeof IndexRoute
  '': typeof LayoutRouteWithChildren
  '/analytics': typeof LayoutAnalyticsLayoutModelsRouteWithChildren
  '/data': typeof LayoutDataLayoutDatasourcesRouteWithChildren
  '/models': typeof LayoutModelsLayoutModelsRouteWithChildren
  '/sessions/$sessionId': typeof LayoutSessionsSessionIdRoute
  '/sessions': typeof LayoutSessionsIndexRoute
  '/data/$dataSourceId': typeof LayoutDataLayoutDatasourcesDataSourceIdRoute
  '/analytics/': typeof LayoutAnalyticsLayoutModelsIndexRoute
  '/data/': typeof LayoutDataLayoutDatasourcesIndexRoute
  '/models/': typeof LayoutModelsLayoutModelsIndexRoute
}

export interface FileRoutesByTo {
  '/': typeof IndexRoute
  '': typeof LayoutRouteWithChildren
  '/analytics': typeof LayoutAnalyticsLayoutModelsIndexRoute
  '/data': typeof LayoutDataLayoutDatasourcesIndexRoute
  '/models': typeof LayoutModelsLayoutModelsIndexRoute
  '/sessions/$sessionId': typeof LayoutSessionsSessionIdRoute
  '/sessions': typeof LayoutSessionsIndexRoute
  '/data/$dataSourceId': typeof LayoutDataLayoutDatasourcesDataSourceIdRoute
}

export interface FileRoutesById {
  __root__: typeof rootRoute
  '/': typeof IndexRoute
  '/_layout': typeof LayoutRouteWithChildren
  '/_layout/analytics': typeof LayoutAnalyticsRouteWithChildren
  '/_layout/analytics/_layout-models': typeof LayoutAnalyticsLayoutModelsRouteWithChildren
  '/_layout/data': typeof LayoutDataRouteWithChildren
  '/_layout/data/_layout-datasources': typeof LayoutDataLayoutDatasourcesRouteWithChildren
  '/_layout/models': typeof LayoutModelsRouteWithChildren
  '/_layout/models/_layout-models': typeof LayoutModelsLayoutModelsRouteWithChildren
  '/_layout/sessions/$sessionId': typeof LayoutSessionsSessionIdRoute
  '/_layout/sessions/': typeof LayoutSessionsIndexRoute
  '/_layout/data/_layout-datasources/$dataSourceId': typeof LayoutDataLayoutDatasourcesDataSourceIdRoute
  '/_layout/analytics/_layout-models/': typeof LayoutAnalyticsLayoutModelsIndexRoute
  '/_layout/data/_layout-datasources/': typeof LayoutDataLayoutDatasourcesIndexRoute
  '/_layout/models/_layout-models/': typeof LayoutModelsLayoutModelsIndexRoute
}

export interface FileRouteTypes {
  fileRoutesByFullPath: FileRoutesByFullPath
  fullPaths:
    | '/'
    | ''
    | '/analytics'
    | '/data'
    | '/models'
    | '/sessions/$sessionId'
    | '/sessions'
    | '/data/$dataSourceId'
    | '/analytics/'
    | '/data/'
    | '/models/'
  fileRoutesByTo: FileRoutesByTo
  to:
    | '/'
    | ''
    | '/analytics'
    | '/data'
    | '/models'
    | '/sessions/$sessionId'
    | '/sessions'
    | '/data/$dataSourceId'
  id:
    | '__root__'
    | '/'
    | '/_layout'
    | '/_layout/analytics'
    | '/_layout/analytics/_layout-models'
    | '/_layout/data'
    | '/_layout/data/_layout-datasources'
    | '/_layout/models'
    | '/_layout/models/_layout-models'
    | '/_layout/sessions/$sessionId'
    | '/_layout/sessions/'
    | '/_layout/data/_layout-datasources/$dataSourceId'
    | '/_layout/analytics/_layout-models/'
    | '/_layout/data/_layout-datasources/'
    | '/_layout/models/_layout-models/'
  fileRoutesById: FileRoutesById
}

export interface RootRouteChildren {
  IndexRoute: typeof IndexRoute
  LayoutRoute: typeof LayoutRouteWithChildren
}

const rootRouteChildren: RootRouteChildren = {
  IndexRoute: IndexRoute,
  LayoutRoute: LayoutRouteWithChildren,
}

export const routeTree = rootRoute
  ._addFileChildren(rootRouteChildren)
  ._addFileTypes<FileRouteTypes>()

/* ROUTE_MANIFEST_START
{
  "routes": {
    "__root__": {
      "filePath": "__root.tsx",
      "children": [
        "/",
        "/_layout"
      ]
    },
    "/": {
      "filePath": "index.tsx"
    },
    "/_layout": {
      "filePath": "_layout.tsx",
      "children": [
        "/_layout/analytics",
        "/_layout/data",
        "/_layout/models",
        "/_layout/sessions/$sessionId",
        "/_layout/sessions/"
      ]
    },
    "/_layout/analytics": {
      "filePath": "_layout/analytics",
      "parent": "/_layout",
      "children": [
        "/_layout/analytics/_layout-models"
      ]
    },
    "/_layout/analytics/_layout-models": {
      "filePath": "_layout/analytics/_layout-models.tsx",
      "parent": "/_layout/analytics",
      "children": [
        "/_layout/analytics/_layout-models/"
      ]
    },
    "/_layout/data": {
      "filePath": "_layout/data",
      "parent": "/_layout",
      "children": [
        "/_layout/data/_layout-datasources"
      ]
    },
    "/_layout/data/_layout-datasources": {
      "filePath": "_layout/data/_layout-datasources.tsx",
      "parent": "/_layout/data",
      "children": [
        "/_layout/data/_layout-datasources/$dataSourceId",
        "/_layout/data/_layout-datasources/"
      ]
    },
    "/_layout/models": {
      "filePath": "_layout/models",
      "parent": "/_layout",
      "children": [
        "/_layout/models/_layout-models"
      ]
    },
    "/_layout/models/_layout-models": {
      "filePath": "_layout/models/_layout-models.tsx",
      "parent": "/_layout/models",
      "children": [
        "/_layout/models/_layout-models/"
      ]
    },
    "/_layout/sessions/$sessionId": {
      "filePath": "_layout/sessions/$sessionId.tsx",
      "parent": "/_layout"
    },
    "/_layout/sessions/": {
      "filePath": "_layout/sessions/index.tsx",
      "parent": "/_layout"
    },
    "/_layout/data/_layout-datasources/$dataSourceId": {
      "filePath": "_layout/data/_layout-datasources/$dataSourceId.tsx",
      "parent": "/_layout/data/_layout-datasources"
    },
    "/_layout/analytics/_layout-models/": {
      "filePath": "_layout/analytics/_layout-models/index.tsx",
      "parent": "/_layout/analytics/_layout-models"
    },
    "/_layout/data/_layout-datasources/": {
      "filePath": "_layout/data/_layout-datasources/index.tsx",
      "parent": "/_layout/data/_layout-datasources"
    },
    "/_layout/models/_layout-models/": {
      "filePath": "_layout/models/_layout-models/index.tsx",
      "parent": "/_layout/models/_layout-models"
    }
  }
}
ROUTE_MANIFEST_END */
