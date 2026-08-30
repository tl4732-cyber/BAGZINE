import { assetUrl } from "./assets";

const DEFAULT_IMAGE = assetUrl("images/bag-placeholder.svg");

const BAG_IMAGE_DIR = assetUrl("images/bags");

const MODEL_IMAGE_FILES: Record<string, string> = {
  "Celine::Luggage": "Celine Luggage.png",
  "Chanel::Boy Bag": "Chanel boy.png",
  "Chanel::Classic Flap": "Chanel classic flap.png",
  "Chanel::Classic Double Flap": "Chanel Classic Double Flap.png",
  "Dior::Lady Dior": "Dior Lady Dior.png",
  "Dior::Saddle": "Dior Saddle.png",
  "Fendi::Baguette": "Fendi Baguette .avif",
  "Fendi::Peekaboo": "Fendi Peekaboo.avif",
  "Gucci::Dionysus": "Gucci Dionysus.png",
  "Gucci::Marmont": "Gucci Marmont.avif",
  "Hermès::Birkin": "Hermès Birkin.png",
  "Hermès::Kelly": "Hermes Kelly.png",
  "Hermès::Constance": "Hermes Constance.png",
  "Hermès::Haut à Courroies": "Hermès Haut à Courroies.png",
  "Hermès::Vinyl Kelly": "Hermès Vinyl Kelly.png",
  "Hermès::Picotin": "Hermès Picotin.png",
  "Hermès::Evelyne": "Hermès Evelyne.png",
  "Hermès::Lindy": "Hermès Lindy.png",
  "Louis Vuitton::Alma": "Louis Vuitton Alma.png",
  "Louis Vuitton::Neverfull": "Louis Vuitton Neverfull.png",
  "Louis Vuitton::Pochette Métis": "Louis Vuitton Pochette Métis.png",
  "Louis Vuitton::Speedy": "Louis Vuitton Speedy.avif",
  "Prada::Galleria": "Prada Galleria.avif",
  "Saint Laurent::Loulou": "Saint Laurent Loulou.png",
};

function modelKey(brand: string, model: string) {
  return `${brand}::${model}`;
}

export function getModelImage(brand: string, model: string): string {
  const file = MODEL_IMAGE_FILES[modelKey(brand, model)];
  if (!file) {
    return DEFAULT_IMAGE;
  }
  return `${BAG_IMAGE_DIR}/${encodeURIComponent(file)}`;
}

/** Per-model scale tweaks when source art has extra padding or odd framing. */
const MODEL_IMAGE_SCALE: Record<string, number> = {};

export function getModelImageScale(brand: string, model: string): number {
  return MODEL_IMAGE_SCALE[modelKey(brand, model)] ?? 1;
}

export function modelExplorePath(brand: string, model: string): string {
  return `/explore/${encodeURIComponent(brand)}/${encodeURIComponent(model)}`;
}

export function brandSectionId(brand: string): string {
  return `brand-${encodeURIComponent(brand)}`;
}

export const PLACEHOLDER_IMAGE = DEFAULT_IMAGE;
