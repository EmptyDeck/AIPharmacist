import React from "react";
import { Link } from "react-router-dom";
export default function MainPage() {
  return (
    <>
      <Link to={`/chat`}>Dr. Watson 시작하기</Link>
    </>
  );
}
