import { Route, Routes } from 'react-router-dom'
import { AdminLayout } from './components/admin/AdminLayout'
import { AdminRoute } from './components/admin/AdminRoute'
import { Layout } from './components/Layout'
import { CustomerRoute, ProtectedRoute } from './components/ProtectedRoute'
import { AccountPage } from './pages/AccountPage'
import { AdminCategoriesPage } from './pages/admin/AdminCategoriesPage'
import { AdminCustomersPage } from './pages/admin/AdminCustomersPage'
import { AdminDashboardPage } from './pages/admin/AdminDashboardPage'
import { AdminOrdersPage } from './pages/admin/AdminOrdersPage'
import { AdminProductsPage } from './pages/admin/AdminProductsPage'
import { CartPage } from './pages/CartPage'
import { HomePage } from './pages/HomePage'
import { LikesPage } from './pages/LikesPage'
import { NotFoundPage } from './pages/NotFoundPage'
import { OrdersPage } from './pages/OrdersPage'
import { ProductPage } from './pages/ProductPage'
import { RegisterPage } from './pages/RegisterPage'
import { ShopPage } from './pages/ShopPage'
import { SignInPage } from './pages/SignInPage'
import './App.css'

function AdminSection() {
  return (
    <AdminRoute>
      <AdminLayout>
        <Routes>
          <Route index element={<AdminDashboardPage />} />
          <Route path="products" element={<AdminProductsPage />} />
          <Route path="categories" element={<AdminCategoriesPage />} />
          <Route path="orders" element={<AdminOrdersPage />} />
          <Route path="customers" element={<AdminCustomersPage />} />
        </Routes>
      </AdminLayout>
    </AdminRoute>
  )
}

function App() {
  return (
    <Routes>
      <Route path="/admin/*" element={<AdminSection />} />
      <Route
        path="*"
        element={
          <Layout>
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/shop" element={<ShopPage />} />
              <Route path="/product/:id" element={<ProductPage />} />
              <Route
                path="/cart"
                element={
                  <CustomerRoute>
                    <CartPage />
                  </CustomerRoute>
                }
              />
              <Route
                path="/orders"
                element={
                  <CustomerRoute>
                    <OrdersPage />
                  </CustomerRoute>
                }
              />
              <Route
                path="/likes"
                element={
                  <CustomerRoute>
                    <LikesPage />
                  </CustomerRoute>
                }
              />
              <Route
                path="/account"
                element={
                  <ProtectedRoute>
                    <AccountPage />
                  </ProtectedRoute>
                }
              />
              <Route path="/signin" element={<SignInPage />} />
              <Route path="/register" element={<RegisterPage />} />
              <Route path="*" element={<NotFoundPage />} />
            </Routes>
          </Layout>
        }
      />
    </Routes>
  )
}

export default App
