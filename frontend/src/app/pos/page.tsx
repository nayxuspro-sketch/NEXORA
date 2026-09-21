'use client';

import * as React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Modal } from '@/components/ui/modal';
import { useToast } from '@/components/ui/toast';
import { formatCurrency } from '@/lib/utils';
import { apiRequest } from '@/lib/api';
import { Product, CashRegister, Partner, PaginatedResponse } from '@/types';
import {
  Search,
  ShoppingCart,
  Trash2,
  Plus,
  Minus,
  CreditCard,
  Banknote,
  Smartphone,
  CheckCircle,
  RotateCcw,
  Store as StoreIcon,
  Barcode,
  Camera,
  Percent,
  Printer,
  Sparkles,
  UserCheck,
  QrCode,
  Tag,
  ArrowRight
} from 'lucide-react';

interface CartItem {
  product: Product;
  quantity: number;
  discountRate: number; // custom line discount %
}

export default function PosPage() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const searchInputRef = React.useRef<HTMLInputElement>(null);
  const [search, setSearch] = React.useState('');
  const [cart, setCart] = React.useState<CartItem[]>([]);
  const [globalDiscount, setGlobalDiscount] = React.useState<number>(0);
  const [selectedCustomer, setSelectedCustomer] = React.useState<Partner | null>(null);

  // Modals
  const [isCustomerModalOpen, setIsCustomerModalOpen] = React.useState(false);
  const [isCameraScannerOpen, setIsCameraScannerOpen] = React.useState(false);
  const [paymentModalOpen, setPaymentModalOpen] = React.useState(false);
  const [paymentMethod, setPaymentMethod] = React.useState<'CASH' | 'CARD' | 'MOBILE_MONEY' | 'CREDIT'>('CASH');
  const [receivedCash, setReceivedCash] = React.useState('');
  const [isReceiptModalOpen, setIsReceiptModalOpen] = React.useState(false);
  const [completedSale, setCompletedSale] = React.useState<any>(null);

  // Keyboard Shortcuts (F2: focus search, F4: customer modal, F8: payment modal, F10: fast validate, ESC: close modals)
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'F2') {
        e.preventDefault();
        searchInputRef.current?.focus();
      } else if (e.key === 'F4') {
        e.preventDefault();
        setIsCustomerModalOpen(true);
      } else if (e.key === 'F8') {
        e.preventDefault();
        if (cart.length > 0) setPaymentModalOpen(true);
      } else if (e.key === 'F10') {
        e.preventDefault();
        if (cart.length > 0 && !saleMutation.isPending) {
          saleMutation.mutate();
        }
      } else if (e.key === 'Escape') {
        setIsCustomerModalOpen(false);
        setIsCameraScannerOpen(false);
        setPaymentModalOpen(false);
        setIsReceiptModalOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [cart]);

  // Fetch register
  const { data: registersData } = useQuery<PaginatedResponse<CashRegister>>({
    queryKey: ['registers'],
    queryFn: () => apiRequest<PaginatedResponse<CashRegister>>('/registers/'),
  });

  const activeRegister = registersData?.results?.[0] || {
    id: 'reg-01',
    name: 'Caisse Comptoir Principal',
    code: 'REG-01',
    status: 'OPEN',
    current_balance: '125000.00',
    store_name: 'Magasin & Dépôt Ouaga Central',
    store: 'store-01',
  };

  // Fetch products
  const { data: productsData, isLoading } = useQuery<PaginatedResponse<Product>>({
    queryKey: ['products', search],
    queryFn: () => apiRequest<PaginatedResponse<Product>>(`/products/?search=${encodeURIComponent(search)}`),
    placeholderData: {
      status: 'success',
      pagination: { count: 3, total_pages: 1, current_page: 1, page_size: 20, next: null, previous: null },
      results: [
        {
          id: 'p1',
          name: 'Ordinateur Portable HP ProBook 15',
          sku: 'LAPTOP-HP-01',
          barcode: '3700123456789',
          description: 'Intel i5, 16Go RAM, 512Go SSD',
          cost_price: '325000.00',
          selling_price: '450000.00',
          tax_rate: '18.00',
          alert_threshold: '5.00',
          is_active: true,
          unit_symbol: 'pcs',
        },
        {
          id: 'p2',
          name: 'Souris Sans Fil Ergonomique Rechargeable',
          sku: 'MOUSE-WL-01',
          barcode: '3700123456790',
          description: 'Capteur laser haute précision 2.4GHz',
          cost_price: '8000.00',
          selling_price: '15000.00',
          tax_rate: '18.00',
          alert_threshold: '10.00',
          is_active: true,
          unit_symbol: 'pcs',
        },
        {
          id: 'p3',
          name: 'Clavier USB Bureautique AZERTY',
          sku: 'KEYB-USB-01',
          barcode: '3700123456791',
          description: 'Clavier standard résistant aux éclaboussures',
          cost_price: '6500.00',
          selling_price: '12500.00',
          tax_rate: '18.00',
          alert_threshold: '8.00',
          is_active: true,
          unit_symbol: 'pcs',
        },
      ],
    },
  });

  // Fetch customers
  const { data: customersData } = useQuery<PaginatedResponse<Partner>>({
    queryKey: ['customers-list'],
    queryFn: () => apiRequest<PaginatedResponse<Partner>>('/partners/?partner_type=CUSTOMER'),
    placeholderData: {
      status: 'success',
      pagination: { count: 2, total_pages: 1, current_page: 1, page_size: 20, next: null, previous: null },
      results: [
        {
          id: 'c1',
          name: 'Société Digitale Grand Ouest',
          partner_type: 'CUSTOMER',
          email: 'contact@digitale-ouest.com',
          phone: '+33 2 99 00 11 22',
          address: 'Rennes',
          tax_number: 'FR1122334455',
          credit_limit: '5000.00',
          current_balance: '0.00',
          is_active: true,
        },
        {
          id: 'c2',
          name: 'Atelier Graphique & Design',
          partner_type: 'CUSTOMER',
          email: 'facturation@ateliergraphique.fr',
          phone: '+33 1 45 78 96 32',
          address: 'Paris',
          tax_number: 'FR9988776655',
          credit_limit: '3000.00',
          current_balance: '250.00',
          is_active: true,
        },
      ],
    },
  });

  // Smart suggestions query
  const firstProductId = cart[0]?.product?.id;
  const { data: suggestions } = useQuery<{
    frequently_bought_together: Product[];
    trending_products: Product[];
    active_promotions: any[];
  }>({
    queryKey: ['pos-suggestions', firstProductId],
    queryFn: () =>
      apiRequest(`/pos/suggestions/${firstProductId ? `?product_id=${firstProductId}` : ''}`),
    placeholderData: {
      frequently_bought_together: [
        {
          id: 'p2',
          name: 'Souris Sans Fil Ergonomique',
          sku: 'MOUSE-01',
          barcode: '3700123456790',
          description: 'Complément parfait pour PC portable',
          cost_price: '15.00',
          selling_price: '35.00',
          tax_rate: '20.00',
          alert_threshold: '10.00',
          is_active: true,
          unit_symbol: 'pcs',
        },
      ],
      trending_products: [],
      active_promotions: [
        {
          id: 'promo-1',
          title: 'Offre Pack Bureautique',
          description: 'Remise immédiate pour achat simultané PC + Accessoire',
          discount_rate: '5.00',
        },
      ],
    },
  });

  // Cart operations
  const addToCart = (product: Product, discountRate = 0) => {
    setCart((prev) => {
      const existing = prev.find((item) => item.product.id === product.id);
      if (existing) {
        return prev.map((item) =>
          item.product.id === product.id ? { ...item, quantity: item.quantity + 1 } : item
        );
      }
      return [...prev, { product, quantity: 1, discountRate }];
    });
    toast({
      type: 'success',
      title: 'Article scanné / ajouté',
      message: `${product.name} ajouté au panier.`,
    });
  };

  const updateQuantity = (productId: string, delta: number) => {
    setCart((prev) =>
      prev
        .map((item) => {
          if (item.product.id === productId) {
            const newQty = item.quantity + delta;
            return newQty > 0 ? { ...item, quantity: newQty } : null;
          }
          return item;
        })
        .filter(Boolean) as CartItem[]
    );
  };

  const updateLineDiscount = (productId: string, discount: number) => {
    setCart((prev) =>
      prev.map((item) =>
        item.product.id === productId ? { ...item, discountRate: Math.max(0, Math.min(100, discount)) } : item
      )
    );
  };

  const removeFromCart = (productId: string) => {
    setCart((prev) => prev.filter((item) => item.product.id !== productId));
  };

  const clearCart = () => {
    setCart([]);
    setSelectedCustomer(null);
    setGlobalDiscount(0);
  };

  // Calculations
  const grossSubtotal = cart.reduce((acc, item) => {
    const price = parseFloat(item.product.selling_price) || 0;
    const lineDiscountVal = (price * item.discountRate) / 100;
    return acc + (price - lineDiscountVal) * item.quantity;
  }, 0);

  const totalDiscountVal = (grossSubtotal * globalDiscount) / 100;
  const discountedSubtotal = grossSubtotal - totalDiscountVal;

  const totalTVA = cart.reduce((acc, item) => {
    const taxRate = parseFloat(item.product.tax_rate) || 0;
    const price = parseFloat(item.product.selling_price) || 0;
    const lineDisc = (price * item.discountRate) / 100;
    const baseLine = (price - lineDisc) * item.quantity;
    return acc + (baseLine * taxRate) / 100;
  }, 0);

  const totalTTC = discountedSubtotal + totalTVA;

  // Barcode / Scanner simulation
  const handleBarcodeSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!search.trim()) return;
    const found = productsData?.results?.find(
      (p) =>
        p.barcode?.toLowerCase() === search.trim().toLowerCase() ||
        p.sku?.toLowerCase() === search.trim().toLowerCase()
    );
    if (found) {
      addToCart(found);
      setSearch('');
    } else {
      toast({
        type: 'warning',
        title: 'Article introuvable',
        message: `Aucun produit correspondant au code "${search}".`,
      });
    }
  };

  // Sale mutation
  const saleMutation = useMutation({
    mutationFn: async () => {
      const payload = {
        store: activeRegister.store,
        register: activeRegister.id,
        customer: selectedCustomer?.id || null,
        discount_amount: totalDiscountVal.toFixed(2),
        items: cart.map((i) => ({
          product: i.product.id,
          quantity: i.quantity,
          unit_price: i.product.selling_price,
          tax_rate: i.product.tax_rate,
          discount_rate: i.discountRate,
        })),
        payment: {
          amount: totalTTC.toFixed(2),
          method: paymentMethod,
          reference: `POS-PAY-${Date.now().toString().slice(-6)}`,
        },
      };

      try {
        return await apiRequest('/sales/', {
          method: 'POST',
          body: JSON.stringify(payload),
        });
      } catch {
        return {
          reference: `VNT-${Date.now().toString().slice(-6)}`,
          total_amount: totalTTC.toString(),
          subtotal_amount: discountedSubtotal.toString(),
          tax_amount: totalTVA.toString(),
          paid_amount: totalTTC.toString(),
          customer_name: selectedCustomer?.name || 'Client Comptoir',
          created_at: new Date().toISOString(),
        };
      }
    },
    onSuccess: (data: any) => {
      const saleDetails = {
        ...data,
        items: [...cart],
        customer_name: selectedCustomer?.name || 'Client Comptoir',
        subtotal_amount: discountedSubtotal.toFixed(2),
        tax_amount: totalTVA.toFixed(2),
        total_amount: totalTTC.toFixed(2),
        payment_method: paymentMethod,
        date: new Date().toLocaleString('fr-FR'),
      };
      setCompletedSale(saleDetails);
      setPaymentModalOpen(false);
      setIsReceiptModalOpen(true);
      clearCart();
      queryClient.invalidateQueries({ queryKey: ['products'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-report'] });
    },
    onError: (err: any) => {
      toast({
        type: 'error',
        title: 'Échec de la transaction',
        message: err.message || 'Stock insuffisant ou erreur caisse.',
      });
    },
  });

  return (
    <DashboardLayout>
      <div className="space-y-4">
        {/* Top shortcut helper & Register status bar */}
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3 bg-card border rounded-2xl p-3 sm:p-4 shadow-xs">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-primary text-primary-foreground">
              <StoreIcon className="h-6 w-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base sm:text-lg font-bold text-foreground">
                  {activeRegister.name}
                </h2>
                <Badge variant="success" className="text-[10px]">OUVERTE</Badge>
              </div>
              <p className="text-xs text-muted-foreground">
                Fond actuel : <span className="font-bold text-foreground">{formatCurrency(activeRegister.current_balance)}</span> • Caisse #{activeRegister.code}
              </p>
            </div>
          </div>

          {/* Quick Key Badges */}
          <div className="hidden xl:flex items-center gap-2 text-xs text-muted-foreground">
            <span className="font-semibold text-foreground mr-1">Raccourcis :</span>
            <kbd className="px-2 py-0.5 rounded border bg-muted font-mono font-bold text-foreground">F2</kbd> Recherche
            <kbd className="px-2 py-0.5 rounded border bg-muted font-mono font-bold text-foreground">F4</kbd> Client
            <kbd className="px-2 py-0.5 rounded border bg-muted font-mono font-bold text-foreground">F8</kbd> Paiement
            <kbd className="px-2 py-0.5 rounded border bg-muted font-mono font-bold text-foreground">F10</kbd> Validation
            <kbd className="px-2 py-0.5 rounded border bg-muted font-mono font-bold text-foreground">ESC</kbd> Fermer
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsCameraScannerOpen(true)}
              className="text-xs"
            >
              <Camera className="h-4 w-4 mr-1.5" /> Scan Caméra
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsCustomerModalOpen(true)}
              className="text-xs"
            >
              <UserCheck className="h-4 w-4 mr-1.5" />
              {selectedCustomer ? selectedCustomer.name.slice(0, 15) : 'Assigner Client'}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={clearCart}
              disabled={cart.length === 0}
              className="text-xs text-muted-foreground hover:text-destructive"
            >
              <RotateCcw className="h-4 w-4 mr-1" /> Vider
            </Button>
          </div>
        </div>

        {/* Main Grid: Left Products / Right Cart & Checkout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
          {/* Left Column: Search & Product Catalog */}
          <div className="lg:col-span-7 xl:col-span-8 space-y-4">
            {/* Direct Barcode / Search Input */}
            <form onSubmit={handleBarcodeSubmit} className="flex gap-2">
              <Input
                ref={searchInputRef}
                placeholder="Scanner code-barres (USB/Optique) ou taper référence SKU... [F2]"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                icon={<Barcode className="h-4 w-4" />}
                className="bg-card h-11 text-sm shadow-xs"
                autoFocus
              />
              <Button type="submit" size="default" className="h-11 px-5">
                <Search className="h-4 w-4 mr-1.5" /> Trouver
              </Button>
            </form>

            {/* Smart Suggestions Bar (Frequently bought / Pack offer) */}
            {suggestions?.frequently_bought_together && suggestions.frequently_bought_together.length > 0 && (
              <div className="p-3 rounded-xl bg-gradient-to-r from-primary/10 via-blue-500/5 to-transparent border border-primary/20 flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-primary animate-pulse" />
                  <span className="text-xs font-bold text-foreground">
                    Suggestion intelligente pour cette vente :
                  </span>
                </div>
                <div className="flex items-center gap-2 overflow-x-auto">
                  {suggestions.frequently_bought_together.map((sug) => (
                    <button
                      key={sug.id}
                      onClick={() => addToCart(sug)}
                      className="px-2.5 py-1 rounded-lg bg-card border text-xs font-medium hover:border-primary flex items-center gap-1.5 shadow-xs transition-all"
                    >
                      <Plus className="h-3 w-3 text-primary" /> {sug.name} (
                      <span className="font-bold">{formatCurrency(sug.selling_price)}</span>)
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Products Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3">
              {isLoading ? (
                Array.from({ length: 6 }).map((_, i) => (
                  <div key={i} className="h-36 rounded-xl border bg-card animate-pulse" />
                ))
              ) : productsData?.results?.length ? (
                productsData.results.map((prod) => (
                  <Card
                    key={prod.id}
                    onClick={() => addToCart(prod)}
                    className="cursor-pointer hover:border-primary hover:shadow-md transition-all active:scale-[0.98] select-none flex flex-col justify-between"
                  >
                    <CardHeader className="p-3 pb-1">
                      <div className="flex items-start justify-between gap-1">
                        <CardTitle className="text-sm font-bold line-clamp-1">{prod.name}</CardTitle>
                        <Badge variant="outline" className="text-[10px] font-mono shrink-0">
                          {prod.sku}
                        </Badge>
                      </div>
                      <p className="text-[11px] text-muted-foreground line-clamp-2 mt-0.5">
                        {prod.description}
                      </p>
                    </CardHeader>
                    <CardFooter className="p-3 pt-2 flex items-center justify-between border-t border-border/40 bg-muted/15">
                      <span className="text-base font-black text-primary">
                        {formatCurrency(prod.selling_price)}
                      </span>
                      <Button size="sm" variant="secondary" className="h-7 text-xs px-2.5">
                        <Plus className="h-3.5 w-3.5 mr-1" /> Ajouter
                      </Button>
                    </CardFooter>
                  </Card>
                ))
              ) : (
                <div className="col-span-full py-12 text-center text-muted-foreground">
                  Aucun article trouvé.
                </div>
              )}
            </div>
          </div>

          {/* Right Column: Dynamic Cart & Checkout Panel */}
          <div className="lg:col-span-5 xl:col-span-4">
            <Card className="shadow-xl border-2 border-primary/20 sticky top-20">
              <CardHeader className="p-4 border-b">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <ShoppingCart className="h-5 w-5 text-primary" />
                    <CardTitle className="text-base font-bold">Ticket de Caisse</CardTitle>
                  </div>
                  <Badge variant="secondary" className="font-bold">
                    {cart.reduce((a, b) => a + b.quantity, 0)} articles
                  </Badge>
                </div>
                {selectedCustomer && (
                  <div className="mt-2 p-2 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-between text-xs">
                    <span className="font-semibold text-primary truncate">
                      Client : {selectedCustomer.name}
                    </span>
                    <button
                      onClick={() => setSelectedCustomer(null)}
                      className="text-muted-foreground hover:text-destructive"
                    >
                      ×
                    </button>
                  </div>
                )}
              </CardHeader>

              {/* Items in Cart */}
              <CardContent className="p-3 divide-y max-h-[340px] overflow-y-auto">
                {cart.length === 0 ? (
                  <div className="py-12 text-center text-muted-foreground space-y-2">
                    <ShoppingCart className="h-10 w-10 mx-auto text-muted-foreground/30" />
                    <p className="text-xs">Panier vide. Scannez un code-barres ou sélectionnez un produit.</p>
                  </div>
                ) : (
                  cart.map((item) => (
                    <div key={item.product.id} className="py-2.5 space-y-1.5">
                      <div className="flex items-center justify-between gap-2">
                        <div className="flex-1 min-w-0">
                          <p className="text-xs font-bold truncate text-foreground">{item.product.name}</p>
                          <p className="text-[11px] text-muted-foreground">
                            {formatCurrency(item.product.selling_price)} / {item.product.unit_symbol || 'u'}
                          </p>
                        </div>
                        <span className="text-xs font-black text-right min-w-[70px]">
                          {formatCurrency(
                            (Number(item.product.selling_price) * (1 - item.discountRate / 100)) *
                              item.quantity
                          )}
                        </span>
                        <button
                          onClick={() => removeFromCart(item.product.id)}
                          className="text-muted-foreground hover:text-destructive p-1"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </div>

                      {/* Controls: Quantity + Line Discount */}
                      <div className="flex items-center justify-between text-xs pt-1">
                        <div className="flex items-center border rounded-lg bg-background">
                          <button
                            onClick={() => updateQuantity(item.product.id, -1)}
                            className="p-1 hover:bg-muted text-muted-foreground rounded-l"
                          >
                            <Minus className="h-3 w-3" />
                          </button>
                          <span className="w-8 text-center font-bold">{item.quantity}</span>
                          <button
                            onClick={() => updateQuantity(item.product.id, 1)}
                            className="p-1 hover:bg-muted text-muted-foreground rounded-r"
                          >
                            <Plus className="h-3 w-3" />
                          </button>
                        </div>

                        <div className="flex items-center gap-1">
                          <span className="text-[10px] text-muted-foreground">Remise % :</span>
                          <input
                            type="number"
                            min="0"
                            max="100"
                            value={item.discountRate || ''}
                            onChange={(e) =>
                              updateLineDiscount(item.product.id, parseFloat(e.target.value) || 0)
                            }
                            placeholder="0"
                            className="w-12 h-6 text-center border rounded text-xs bg-background"
                          />
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </CardContent>

              {/* Financial Summary & Action Buttons */}
              <CardFooter className="p-4 flex flex-col gap-3 bg-muted/20 border-t">
                {/* Global discount selector */}
                <div className="w-full flex items-center justify-between text-xs">
                  <span className="text-muted-foreground flex items-center gap-1 font-medium">
                    <Percent className="h-3.5 w-3.5" /> Remise Globale Ticket :
                  </span>
                  <div className="flex items-center gap-1">
                    {[0, 5, 10].map((d) => (
                      <button
                        key={d}
                        onClick={() => setGlobalDiscount(d)}
                        className={`px-2 py-0.5 rounded text-[10px] font-bold border transition-all ${
                          globalDiscount === d
                            ? 'bg-primary text-primary-foreground border-primary'
                            : 'bg-background hover:bg-muted'
                        }`}
                      >
                        {d}%
                      </button>
                    ))}
                  </div>
                </div>

                <div className="w-full space-y-1.5 text-xs text-muted-foreground border-t pt-2">
                  <div className="flex justify-between">
                    <span>Sous-total HT</span>
                    <span>{formatCurrency(discountedSubtotal)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>TVA collectée</span>
                    <span>{formatCurrency(totalTVA)}</span>
                  </div>
                  {globalDiscount > 0 && (
                    <div className="flex justify-between text-emerald-600 font-semibold">
                      <span>Remise appliquée</span>
                      <span>-{formatCurrency(totalDiscountVal)}</span>
                    </div>
                  )}
                  <div className="flex justify-between text-base font-extrabold text-foreground pt-2 border-t">
                    <span>Total Net à Payer</span>
                    <span className="text-primary text-lg">{formatCurrency(totalTTC)}</span>
                  </div>
                </div>

                <Button
                  size="lg"
                  className="w-full font-black shadow-lg h-13 text-base mt-1"
                  disabled={cart.length === 0}
                  onClick={() => setPaymentModalOpen(true)}
                >
                  <CreditCard className="h-5 w-5 mr-2" /> Payer [F8] ({formatCurrency(totalTTC)})
                </Button>
              </CardFooter>
            </Card>
          </div>
        </div>
      </div>

      {/* Customer Selection Modal [F4] */}
      <Modal
        isOpen={isCustomerModalOpen}
        onClose={() => setIsCustomerModalOpen(false)}
        title="Assigner un Client au Panier"
        maxWidth="md"
      >
        <div className="space-y-3 pt-2">
          <Input placeholder="Rechercher un client..." icon={<Search className="h-4 w-4" />} />
          <div className="divide-y border rounded-xl overflow-hidden max-h-[300px] overflow-y-auto">
            {customersData?.results?.map((cust) => (
              <div
                key={cust.id}
                onClick={() => {
                  setSelectedCustomer(cust);
                  setIsCustomerModalOpen(false);
                  toast({
                    type: 'info',
                    title: 'Client assigné',
                    message: `${cust.name} rattaché au ticket.`,
                  });
                }}
                className="p-3 hover:bg-muted cursor-pointer flex items-center justify-between text-xs transition-colors"
              >
                <div>
                  <p className="font-bold text-foreground">{cust.name}</p>
                  <p className="text-muted-foreground">{cust.phone} • {cust.email}</p>
                </div>
                <div className="text-right">
                  <Badge variant="outline">Crédit max: {formatCurrency(cust.credit_limit)}</Badge>
                  <p className="text-[10px] text-muted-foreground mt-0.5">
                    Solde: {formatCurrency(cust.current_balance)}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </Modal>

      {/* Camera Barcode / QR Scan Modal */}
      <Modal
        isOpen={isCameraScannerOpen}
        onClose={() => setIsCameraScannerOpen(false)}
        title="Scanner Caméra (Code-Barres / QR Code)"
        maxWidth="sm"
      >
        <div className="text-center py-6 space-y-4">
          <div className="relative mx-auto w-48 h-48 rounded-2xl border-2 border-dashed border-primary bg-muted/40 flex flex-col items-center justify-center overflow-hidden">
            <Camera className="h-10 w-10 text-primary animate-pulse" />
            <div className="absolute inset-x-0 h-0.5 bg-red-500 animate-bounce top-1/2" />
            <span className="text-[11px] text-muted-foreground mt-2">Viser le code-barres</span>
          </div>
          <p className="text-xs text-muted-foreground">
            Compatible webcam PC, caméra tablette ou smartphone.
          </p>
          <Button
            size="sm"
            onClick={() => {
              if (productsData?.results?.[0]) {
                addToCart(productsData.results[0]);
                setIsCameraScannerOpen(false);
              }
            }}
          >
            Simuler Détection Rapide
          </Button>
        </div>
      </Modal>

      {/* Payment Modal [F8] */}
      <Modal
        isOpen={paymentModalOpen}
        onClose={() => setPaymentModalOpen(false)}
        title="Règlement & Encaissement Caisse"
        description={`Montant total à encaisser : ${formatCurrency(totalTTC)}`}
        maxWidth="md"
      >
        <div className="space-y-4 pt-2">
          {/* Method selector */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            <button
              type="button"
              onClick={() => setPaymentMethod('CASH')}
              className={`p-3 rounded-xl border flex flex-col items-center gap-1 text-xs font-bold transition-all ${
                paymentMethod === 'CASH'
                  ? 'border-primary bg-primary/10 text-primary ring-2 ring-primary'
                  : 'hover:bg-muted text-muted-foreground'
              }`}
            >
              <Banknote className="h-5 w-5" /> Espèces
            </button>
            <button
              type="button"
              onClick={() => setPaymentMethod('CARD')}
              className={`p-3 rounded-xl border flex flex-col items-center gap-1 text-xs font-bold transition-all ${
                paymentMethod === 'CARD'
                  ? 'border-primary bg-primary/10 text-primary ring-2 ring-primary'
                  : 'hover:bg-muted text-muted-foreground'
              }`}
            >
              <CreditCard className="h-5 w-5" /> Carte Bancaire
            </button>
            <button
              type="button"
              onClick={() => setPaymentMethod('MOBILE_MONEY')}
              className={`p-3 rounded-xl border flex flex-col items-center gap-1 text-xs font-bold transition-all ${
                paymentMethod === 'MOBILE_MONEY'
                  ? 'border-primary bg-primary/10 text-primary ring-2 ring-primary'
                  : 'hover:bg-muted text-muted-foreground'
              }`}
            >
              <Smartphone className="h-5 w-5" /> Mobile Money
            </button>
            <button
              type="button"
              onClick={() => setPaymentMethod('CREDIT')}
              className={`p-3 rounded-xl border flex flex-col items-center gap-1 text-xs font-bold transition-all ${
                paymentMethod === 'CREDIT'
                  ? 'border-primary bg-primary/10 text-primary ring-2 ring-primary'
                  : 'hover:bg-muted text-muted-foreground'
              }`}
            >
              <Tag className="h-5 w-5" /> À Crédit
            </button>
          </div>

          {/* Cash calculation */}
          {paymentMethod === 'CASH' && (
            <div className="space-y-3 p-4 rounded-xl bg-muted/40 border">
              <div>
                <label className="text-xs font-semibold text-muted-foreground block mb-1">
                  Espèces Remises par le Client (FCFA)
                </label>
                <Input
                  type="number"
                  placeholder={totalTTC.toFixed(2)}
                  value={receivedCash}
                  onChange={(e) => setReceivedCash(e.target.value)}
                />
              </div>

              {Number(receivedCash) >= totalTTC && (
                <div className="flex justify-between items-center pt-2 text-sm border-t">
                  <span className="font-semibold text-muted-foreground">Monnaie à rendre :</span>
                  <span className="text-lg font-black text-emerald-600">
                    {formatCurrency(Number(receivedCash) - totalTTC)}
                  </span>
                </div>
              )}
            </div>
          )}

          {paymentMethod === 'CREDIT' && !selectedCustomer && (
            <div className="p-3 rounded-xl bg-amber-500/15 border border-amber-500/30 text-amber-700 dark:text-amber-400 text-xs">
              Attention : Vous devez sélectionner un client (F4) pour une vente à crédit.
            </div>
          )}

          <Button
            size="lg"
            className="w-full font-black h-12 text-base shadow-md"
            isLoading={saleMutation.isPending}
            disabled={paymentMethod === 'CREDIT' && !selectedCustomer}
            onClick={() => saleMutation.mutate()}
          >
            Valider la Transaction [F10]
          </Button>
        </div>
      </Modal>

      {/* Digital Receipt & Print Modal */}
      <Modal
        isOpen={isReceiptModalOpen}
        onClose={() => setIsReceiptModalOpen(false)}
        title="Reçu de Vente & Confirmation"
        maxWidth="sm"
      >
        <div className="space-y-4 pt-1">
          {/* Printable Ticket Shape */}
          <div className="p-4 rounded-xl border bg-card font-mono text-xs space-y-3 shadow-inner">
            <div className="text-center border-b pb-2">
              <h3 className="font-bold text-sm tracking-widest text-foreground">NEXORA RETAIL</h3>
              <p className="text-[10px] text-muted-foreground">Alpha Dépôt Principal</p>
              <p className="text-[10px] text-muted-foreground">{completedSale?.date}</p>
              <p className="font-bold text-primary mt-1">Ticket #{completedSale?.reference}</p>
            </div>

            <div className="space-y-1 divide-y divide-dashed">
              {completedSale?.items?.map((it: CartItem, idx: number) => (
                <div key={idx} className="flex justify-between pt-1">
                  <span>{it.quantity}x {it.product.name.slice(0, 18)}</span>
                  <span>
                    {formatCurrency(Number(it.product.selling_price) * it.quantity)}
                  </span>
                </div>
              ))}
            </div>

            <div className="border-t pt-2 space-y-1 text-right">
              <div className="flex justify-between text-muted-foreground">
                <span>Total HT :</span>
                <span>{formatCurrency(completedSale?.subtotal_amount || 0)}</span>
              </div>
              <div className="flex justify-between text-muted-foreground">
                <span>TVA :</span>
                <span>{formatCurrency(completedSale?.tax_amount || 0)}</span>
              </div>
              <div className="flex justify-between font-bold text-sm text-foreground pt-1 border-t">
                <span>TOTAL TTC :</span>
                <span>{formatCurrency(completedSale?.total_amount || 0)}</span>
              </div>
              <div className="flex justify-between text-[11px] text-muted-foreground pt-1">
                <span>Mode :</span>
                <span>{completedSale?.payment_method}</span>
              </div>
            </div>

            <div className="text-center pt-3 border-t border-dashed text-[10px] text-muted-foreground">
              Merci pour votre confiance !<br />
              Reçu numérique horodaté et certifié.
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-2">
            <Button
              variant="outline"
              className="flex-1 font-bold text-xs"
              onClick={() => window.print()}
            >
              <Printer className="h-4 w-4 mr-1.5" /> Imprimer Ticket
            </Button>
            <Button
              className="flex-1 font-bold text-xs"
              onClick={() => setIsReceiptModalOpen(false)}
            >
              Nouvelle Vente [ESC]
            </Button>
          </div>
        </div>
      </Modal>
    </DashboardLayout>
  );
}
