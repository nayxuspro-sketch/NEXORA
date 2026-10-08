import * as React from 'react';
import { useRouter } from 'next/navigation';
import { Modal } from '@/components/ui/modal';
import { Input } from '@/components/ui/input';
import { Search, ShoppingCart, Package, Layers, Users, ArrowRight } from 'lucide-react';

interface QuickSearchModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function QuickSearchModal({ isOpen, onClose }: QuickSearchModalProps) {
  const router = useRouter();
  const [query, setQuery] = React.useState('');

  const quickLinks = [
    { name: 'Ouvrir Point de Vente (POS)', href: '/pos', icon: ShoppingCart, category: 'Vente' },
    { name: 'Catalogue & Nouveaux Produits', href: '/products', icon: Package, category: 'Gestion' },
    { name: 'Gestion & Mouvements de Stock', href: '/inventory', icon: Layers, category: 'Stock' },
    { name: 'Répertoire Clients & Fournisseurs', href: '/partners', icon: Users, category: 'Tiers' },
  ];

  const handleSelect = (href: string) => {
    router.push(href);
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Navigation & Recherche Rapide" maxWidth="lg">
      <div className="space-y-4">
        <Input
          placeholder="Rechercher une page, un produit, un raccourci..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          icon={<Search className="h-4 w-4" />}
          autoFocus
        />

        <div className="space-y-1">
          <p className="text-xs font-semibold text-muted-foreground uppercase px-2 mb-2">Raccourcis Fréquents</p>
          {quickLinks.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.name}
                onClick={() => handleSelect(item.href)}
                className="w-full flex items-center justify-between p-3 rounded-lg hover:bg-muted text-left transition-colors group"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-md bg-primary/10 text-primary">
                    <Icon className="h-4 w-4" />
                  </div>
                  <div>
                    <span className="text-sm font-medium text-foreground block">{item.name}</span>
                    <span className="text-xs text-muted-foreground">{item.category}</span>
                  </div>
                </div>
                <ArrowRight className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
              </button>
            );
          })}
        </div>
      </div>
    </Modal>
  );
}
