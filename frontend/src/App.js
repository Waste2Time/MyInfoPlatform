import React, { useEffect, useState } from 'react';
import { Offcanvas, Button } from 'react-bootstrap';
import './App.css';

function Sidebar({ active, onChange, show, onHide }) {
  const items = [
    { key: 'unread', label: '未读文章', icon: 'bi bi-book' },
    { key: 'all', label: '全部文章', icon: 'bi bi-collection' },
    { key: 'read', label: '已读文章', icon: 'bi bi-check-circle' },
    { key: 'starred', label: '收藏文章', icon: 'bi bi-star' },
  ];
  return (
    <Offcanvas show={show} onHide={onHide} placement="start" className="bg-dark text-white">
      <Offcanvas.Header closeButton className="text-white">
        <Offcanvas.Title className="fs-4 fw-bold">MyInfo</Offcanvas.Title>
      </Offcanvas.Header>
      <Offcanvas.Body className="d-flex flex-column">
        <ul className="nav nav-pills flex-column mb-auto">
          {items.map((it) => (
            <li className="nav-item mb-2" key={it.key}>
              <button
                className={`nav-link btn btn-link text-start w-100 text-white ${active === it.key ? 'bg-primary' : 'text-white'}`}
                onClick={() => onChange(it.key)}
              >
                <i className={`${it.icon} me-2`}></i>{it.label}
              </button>
            </li>
          ))}
        </ul>
        <hr className="text-white" />
        <div className="mt-auto small text-muted">示例前端（React + Bootstrap 5）</div>
      </Offcanvas.Body>
    </Offcanvas>
  );
}

function ArticleList({ items, onSelect }) {
  if (!items) return <div className="text-center p-4">加载中……</div>;
  if (items.length === 0) return <div className="text-center p-4 text-muted">暂无文章</div>;
  return (
    <div className="list-group">
      {items.map((it) => (
        <div key={it.id} className="card mb-3 shadow-sm" onClick={() => onSelect(it.id)} style={{ cursor: 'pointer' }}>
          <div className="card-body">
            <div className="d-flex justify-content-between align-items-start">
              <h6 className="card-title mb-1">{it.title}</h6>
              <small className="text-muted">{it.fetched_at ? new Date(it.fetched_at).toLocaleDateString() : ''}</small>
            </div>
            <p className="card-text text-truncate mb-1">{it.summary}</p>
            <small className="text-muted">{it.source_name}</small>
          </div>
        </div>
      ))}
    </div>
  );
}

function ArticleDetail({ item }) {
  if (!item) return <div className="text-center p-4 text-muted">请选择一篇文章以查看详情</div>;
  return (
    <div className="card shadow">
      <div className="card-header bg-light">
        <h5 className="card-title mb-0">{item.title}</h5>
        <small className="text-muted">{item.source_name} · {item.published_at ? new Date(item.published_at).toLocaleString() : ''}</small>
      </div>
      <div className="card-body">
        <div dangerouslySetInnerHTML={{ __html: item.content }} />
      </div>
    </div>
  );
}

function App() {
  const [status, setStatus] = useState('unread');
  const [items, setItems] = useState(null);
  const [selectedId, setSelectedId] = useState(null);
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showSidebar, setShowSidebar] = useState(false);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    fetch(`/rss/?status=${encodeURIComponent(status)}`)
      .then((r) => r.json())
      .then((data) => {
        if (!mounted) return;
        setItems(data);
        setSelectedId(null);
        setDetail(null);
      })
      .catch(() => {
        if (!mounted) return;
        setItems([]);
      })
      .finally(() => mounted && setLoading(false));
    return () => { mounted = false; };
  }, [status]);

  useEffect(() => {
    if (!selectedId) return setDetail(null);
    let mounted = true;
    fetch(`/rss/${selectedId}`)
      .then((r) => {
        if (!r.ok) throw new Error('fetch detail failed');
        return r.json();
      })
      .then((data) => mounted && setDetail(data))
      .catch(() => mounted && setDetail(null));
    return () => { mounted = false; };
  }, [selectedId]);

  return (
    <div className="container-fluid bg-light min-vh-100">
      <div className="row">
        <div className="d-md-none">
          <Button variant="outline-primary" onClick={() => setShowSidebar(true)} className="m-3">
            <i className="bi bi-list"></i> 菜单
          </Button>
        </div>
        <Sidebar active={status} onChange={(key) => { setStatus(key); setShowSidebar(false); }} show={showSidebar} onHide={() => setShowSidebar(false)} />
        <div className="col-md-9 col-lg-10 vh-100 overflow-auto">
          <div className="p-4">
            <h4 className="mb-4 fw-bold">
              <i className={`bi me-2 ${status === 'unread' ? 'bi-book' : status === 'all' ? 'bi-collection' : status === 'read' ? 'bi-check-circle' : 'bi-star'}`}></i>
              {status === 'unread' ? '未读文章' : status === 'all' ? '全部文章' : status === 'read' ? '已读文章' : '收藏文章'}
            </h4>
            <div className="row">
              <div className="col-md-6">
                {loading ? <div className="text-center p-4"><div className="spinner-border text-primary" role="status"><span className="visually-hidden">Loading...</span></div></div> : <ArticleList items={items || []} onSelect={setSelectedId} />}
              </div>
              <div className="col-md-6">
                <ArticleDetail item={detail} />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
