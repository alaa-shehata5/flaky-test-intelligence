import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Dashboard } from './pages/Dashboard';
import { FlakyTests } from './pages/FlakyTests';
import { Runs } from './pages/Runs';
import { TestDetail } from './pages/TestDetail';
import { Tests } from './pages/Tests';

const router = createBrowserRouter([
  {
    path: '/',
    element: <Layout />,
    children: [
      { index: true, element: <Dashboard /> },
      { path: 'tests', element: <Tests /> },
      { path: 'tests/:id', element: <TestDetail /> },
      { path: 'flaky', element: <FlakyTests /> },
      { path: 'runs', element: <Runs /> },
    ],
  },
]);

export default function App() {
  return <RouterProvider router={router} />;
}
