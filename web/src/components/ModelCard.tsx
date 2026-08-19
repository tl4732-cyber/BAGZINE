import { Link } from "react-router-dom";
import type { ModelSummary } from "../types";
import { formatMoney } from "../api";
import { getModelImage, modelExplorePath } from "../lib/modelImages";

interface Props {
  model: ModelSummary;
  showBrand?: boolean;
}

export function ModelCard({ model, showBrand = false }: Props) {
  const imageSrc = getModelImage(model.brand, model.model);

  return (
    <article className="catalog-card">
      <div className="catalog-card-image">
        <img
          src={imageSrc}
          alt={`${model.brand} ${model.model}`}
          className="catalog-card-photo"
          loading="lazy"
          onError={(e) => {
            e.currentTarget.src = "/images/bag-placeholder.svg";
          }}
        />
      </div>

      <div className="catalog-card-body">
        {showBrand && <p className="catalog-card-brand">{model.brand}</p>}
        <p className="catalog-card-model">{model.model}</p>
        <p className="catalog-card-price">
          {formatMoney(model.avg_price, model.currency)}
        </p>
      </div>

      <Link className="catalog-card-action" to={modelExplorePath(model.brand, model.model)}>
        Explore <span aria-hidden>→</span>
      </Link>
    </article>
  );
}
