import { MotionConfig } from 'framer-motion';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { Layout } from './components/Layout';
import { ToastProvider } from './components/Toast';
import Contact from './pages/Contact';
import Founders from './pages/Founders';
import Home from './pages/Home';
import Investors from './pages/Investors';
import NotFound from './pages/NotFound';
import Portfolio from './pages/Portfolio';
import Team from './pages/Team';

const router = createBrowserRouter(
  [
    {
      element: <Layout />,
      children: [
        { path: '/', element: <Home /> },
        { path: '/portfolio', element: <Portfolio /> },
        { path: '/team', element: <Team /> },
        { path: '/founders', element: <Founders /> },
        { path: '/investors', element: <Investors /> },
        { path: '/contact', element: <Contact /> },
        { path: '*', element: <NotFound /> },
      ],
    },
  ],
  { basename: import.meta.env.BASE_URL.replace(/\/$/, '') || '/' },
);

export default function App() {
  return (
    <MotionConfig reducedMotion="user">
      <ToastProvider>
        <RouterProvider router={router} />
      </ToastProvider>
    </MotionConfig>
  );
}
