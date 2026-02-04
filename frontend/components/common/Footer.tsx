import Image from "next/image";

export function Footer() {
  return (
    <footer>
      <div className="footer-content">
        <div className="footer-logo">
          <Image src="/images/logo.png" alt="Logo" width={50} height={50} />
        </div>
        <div className="footer-text">
          <span className="footer-title">낚시금지구역</span>
          <span className="footer-subtitle">no-fishing zone</span>
        </div>
      </div>
    </footer>
  );
}
