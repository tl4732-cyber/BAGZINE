import { useState } from "react";

interface Props {
  imageUrl: string | null | undefined;
  alt: string;
  className?: string;
  unavailableClassName?: string;
}

export function ListingPhoto({
  imageUrl,
  alt,
  className = "listing-card-photo listing-card-photo--listing",
  unavailableClassName = "listing-photo-unavailable",
}: Props) {
  const [failed, setFailed] = useState(false);

  if (!imageUrl || failed) {
    return <p className={unavailableClassName}>Image not available</p>;
  }

  return (
    <img
      src={imageUrl}
      alt={alt}
      className={className}
      loading="lazy"
      onError={() => setFailed(true)}
    />
  );
}
