import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { ScrollToTop } from "./components/ScrollToTop";
import { Layout } from "./components/Layout";
import { BrandPage } from "./pages/BrandPage";
import { ContactPage } from "./pages/ContactPage";
import { CreatorPage } from "./pages/CreatorPage";
import { LandingPage } from "./pages/LandingPage";
import { ListingDetailPage } from "./pages/ListingDetailPage";
import { ModelExplorePage } from "./pages/ModelExplorePage";
import { OverviewPage } from "./pages/OverviewPage";
import {
  AboutPage,
  BlogPage,
  PricingPage,
  TechSpecsPage,
} from "./pages/StaticPage";
import "./index.css";

if ("scrollRestoration" in window.history) {
  window.history.scrollRestoration = "manual";
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <ScrollToTop />
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<LandingPage />} />
          <Route path="prices" element={<OverviewPage />} />
          <Route path="explore/:brand/:model" element={<ModelExplorePage />} />
          <Route path="listings/:id" element={<ListingDetailPage />} />
          <Route path="about" element={<AboutPage />} />
          <Route path="the-brand" element={<BrandPage />} />
          <Route path="tech-specs" element={<TechSpecsPage />} />
          <Route path="the-creator" element={<CreatorPage />} />
          <Route path="contact" element={<ContactPage />} />
          <Route path="blog" element={<BlogPage />} />
          <Route path="pricing" element={<PricingPage />} />
          <Route path="listings" element={<Navigate to="/prices" replace />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);
