const DEFAULT_IMAGE = "/images/bag-placeholder.svg";

const MODEL_IMAGES: Record<string, string> = {
  "Hermès::Birkin":
    "https://images.unsplash.com/photo-1584917865442-de89df76afd3?w=480&h=480&fit=crop&q=80",
  "Hermès::Kelly":
    "https://images.unsplash.com/photo-1590874103328-eac38a683ce7?w=480&h=480&fit=crop&q=80",
  "Hermès::Vinyl Kelly":
    "https://images.unsplash.com/photo-1566150905458-1bf1fc113f0d?w=480&h=480&fit=crop&q=80",
  "Chanel::Classic Flap":
    "https://images.unsplash.com/photo-1548036328-c9fa89d128fa?w=480&h=480&fit=crop&q=80",
  "Chanel::Classic Double Flap":
    "https://images.unsplash.com/photo-1591567180030-f7f1a4a8b8e2?w=480&h=480&fit=crop&q=80",
};

export function getModelImage(brand: string, model: string): string {
  return MODEL_IMAGES[`${brand}::${model}`] ?? DEFAULT_IMAGE;
}

export function modelExplorePath(brand: string, model: string): string {
  return `/explore/${encodeURIComponent(brand)}/${encodeURIComponent(model)}`;
}
