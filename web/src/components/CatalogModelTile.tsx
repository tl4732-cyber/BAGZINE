import { Link } from "react-router-dom";
import type { ModelSummary } from "../types";
import {
  getModelImage,
  getModelImageScale,
  modelExplorePath,
} from "../lib/modelImages";

interface Props {
  model: ModelSummary;
}

export function CatalogModelTile({ model }: Props) {
  const imageSrc = getModelImage(model.brand, model.model);
  const imageScale = getModelImageScale(model.brand, model.model);

  return (
    <Link
      className="catalog-model-tile"
      to={modelExplorePath(model.brand, model.model)}
    >
      <div className="catalog-model-tile-image">
        <img
          src={imageSrc}
          alt={`${model.brand} ${model.model}`}
          loading="lazy"
          style={
            imageScale !== 1
              ? { transform: `scale(${imageScale})`, transformOrigin: "center bottom" }
              : undefined
          }
          onError={(e) => {
            e.currentTarget.src = "/images/bag-placeholder.svg";
          }}
        />
      </div>
      <span className="catalog-model-tile-name">{model.model}</span>
    </Link>
  );
}
