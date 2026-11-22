"use client";

import { useT } from "@/lib/i18n";

const DOLLAR_FOR_URL = "https://dollarfor.org";
const REPO_URL = "https://github.com/MarvinRidgeMT/BillBack";

/** Who made this, what we do with data (nothing), and where the numbers come from. */
export function Footer() {
  const t = useT();
  const external = { target: "_blank", rel: "noopener noreferrer" } as const;
  return (
    <footer className="site-footer">
      <p>
        <span>{t("footer.built")}</span>
        <span aria-hidden="true"> · </span>
        <span>{t("footer.no_store")}</span>
        <span aria-hidden="true"> · </span>
        <span>{t("footer.not_advice")}</span>
        <span aria-hidden="true"> · </span>
        <span>
          {t("footer.free_help")}{" "}
          <a className="text-link" href={DOLLAR_FOR_URL} {...external}>
            Dollar For<span className="sr-only"> {t("result.new_tab")}</span>
          </a>
        </span>
        <span aria-hidden="true"> · </span>
        <a className="text-link" href={REPO_URL} {...external}>
          {t("footer.github")}
          <span className="sr-only"> {t("result.new_tab")}</span>
        </a>
      </p>
      <p className="data-line">{t("footer.data")}</p>
    </footer>
  );
}
