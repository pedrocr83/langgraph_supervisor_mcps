# Database Agent Guide - Misterios Primavera ERP

**Goal**: Fast, accurate querying with minimal retries. Explore first, then query.

---

## 📊 Table Overview

### Header Tables (Document Dates & Metadata)

#### `public.CabecDoc` (0 rows)
- **Date columns**: `data`, `datavencimento`, `dataultimaactualizacao`, `datacarga`, `datadescarga`
- **Join keys**: `entidade`, `localidade`, `codpostallocalidade`, `id`, `idcabectesouraria`
- **Sample columns**: data (text), zona (text), entidade (text), tipodoc (text), numdoc (text), condpag (text), descpag (text), totalmerc (text), totaliva (text), totaldesc (text), totaloutros (text), modoexp (text)

#### `public.CabecDocExtended` (17,306 rows)
- **Join keys**: `idcabecdoc`, `tipoentidadetransporte`, `entidadetransporte`, `transportepropriaentidade`
- **Sample columns**: idcabecdoc (text), tipoentidadetransporte (text), entidadetransporte (text), transportepropriaentidade (text), versaoultact (text), template (text), atcud (text), refcodfiscaldocorig (text)

#### `public.CabecDocTaxFree` (36,964 rows)
- **Date columns**: `datanascimento`
- **Join keys**: `idcabecdoc`, `tipoentidadebroker`
- **Sample columns**: idcabecdoc (text), sujeitotaxfree (text), passaporte (text), paisemissorpassaporte (text), valorcaucao (text), valoriva (text), valordocumento (text), datanascimento (text), tipoentidadebroker (text), broker (text)

#### `public.INV_CabecTransferenciasArtigo` (335 rows)
- **Date columns**: `data`, `dataultimaactualizacao`
- **Join keys**: `id`, `artigoorigem`, `anulaartigo`, `artigodestino`, `idgdoc`
- **Sample columns**: id (text), tipodoc (text), numdoc (text), filial (text), serie (text), moeda (text), cambio (text), cambiomalt (text), cambiombase (text), arredondamento (text), data (text), observacoes (text)

#### `public.DocumentosCBL` (92 rows)
- **Date columns**: `dataintegracaocct`, `datacriacao`
- **Join keys**: `validadupnumdocext`, `validadupnumdocextentidade`
- **Sample columns**: documento (text), descricao (text), diario (text), fluxo (text), recapitulativos (text), descrauto (text), balanalitica (text), balfinanceira (text), balorcamental (text), recolhaterc (text), retencao (text), tipodocimo (text)

#### `public.DocumentosTesouraria` (14 rows)
- **Date columns**: `dataultimaactualizacao`
- **Join keys**: `entidadespublicas`
- **Sample columns**: documento (text), descricao (text), tipo (text), movimentocredito (text), movimentodebito (text), diario (text), fluxo (text), ligacontab (text), visualizarligacaocbl (text), ligacaocblonline (text), classesivacbl (text), centroscustocbl (text)

#### `public.CabecComprasStatus` (9,668 rows)
- **Date columns**: `dataimp`, `dataanulacao`, `dataenviadoemail`
- **Join keys**: `idcabeccompras`, `atdoccodeid`
- **Sample columns**: idcabeccompras (text), docimp (text), movcontab (text), movimobilizado (text), estado (text), anulado (text), fechado (text), versaoultact (text), estadoiec (text), dataimp (text), atdoccodeid (text), motivoanulacao (text)

### Line Tables (Sales / Movements)

#### `public.LinhasDocStatus` (423,864 rows)
- **Join keys**: `idlinhasdoc`, `quantidade`, `egar_apadoccodeid`
- **Quantity columns**: `quantidade`, `quantreserv`, `quanttrans`, `quantcopiada`
- **Sample columns**: idlinhasdoc (text), quantidade (text), quantreserv (text), quanttrans (text), estadotrans (text), estrategia (text), fechado (text), versaoultact (text), quantcopiada (text), egar_apadoccodeid (text), estadoimo (text), observacoes (text)

#### `public.LinhasDoc` (0 rows)
- **Join keys**: `artigo`, `quantidade`, `datasaida`, `precoliquido`, `idcabecdoc`
- **Value columns**: `precoliquido`, `intrastatvalorliq`, `ccustocbl`, `totaliliquido`, `totalda`
- **Quantity columns**: `quantidade`, `cdu_quantidadealternativa`, `cdu_qtdbonus`
- **Sample columns**: numlinha (text), artigo (text), desconto1 (text), desconto2 (text), desconto3 (text), taxaiva (text), codiva (text), quantidade (text), pcm (text), precunit (text), regimeiva (text), data (text)

#### `public.LinhasDocTrans` (127,476 rows)
- **Join keys**: `idlinhasdoc`, `idlinhasdocorigem`
- **Quantity columns**: `quanttrans`
- **Sample columns**: idlinhasdoc (text), idlinhasdocorigem (text), quanttrans (text), versaoultact (text)

#### `public.LinhasComprasStatus` (41,262 rows)
- **Join keys**: `idlinhascompras`, `quantidade`
- **Quantity columns**: `quantidade`, `quantreserv`, `quanttrans`, `quantcopiada`
- **Sample columns**: idlinhascompras (text), quantidade (text), quantreserv (text), quanttrans (text), estadotrans (text), estrategia (text), fechado (text), versaoultact (text), quantcopiada (text), estadoimo (text), observacoes (text)

#### `public.LinhasPendentes` (11,054 rows)
- **Join keys**: `id`, `idhistorico`, `incidencia`, `obraid`, `classeid`
- **Value columns**: `valoriva`, `total`, `ccustocbl`, `valorrecargo`
- **Sample columns**: id (text), idhistorico (text), linha (text), descricao (text), codiva (text), incidencia (text), valoriva (text), total (text), contacbl (text), ccustocbl (text), analiticacbl (text), funcionalcbl (text)

#### `public.LinhasComprasTrans` (8,732 rows)
- **Join keys**: `idlinhascompras`, `idlinhascomprasorigem`
- **Quantity columns**: `quanttrans`
- **Sample columns**: idlinhascompras (text), idlinhascomprasorigem (text), quanttrans (text), versaoultact (text), vpt (text)

#### `public.INV_LinhasTransferenciasArtigo` (337 rows)
- **Join keys**: `id`, `idcabectransferencias`, `quantidade`
- **Value columns**: `precocusto`
- **Quantity columns**: `estadostock`, `quantidade`
- **Sample columns**: id (text), idcabectransferencias (text), numlinha (text), armazem (text), localizacao (text), lote (text), estadostock (text), quantidade (text), precocusto (text), versaoultact (text)

#### `public.LinhasExtractoBancario` (304 rows)
- **Join keys**: `id`, `idcabecextractobancario`
- **Value columns**: `datavalor`, `valormov`, `valorconta`
- **Sample columns**: id (text), idcabecextractobancario (text), datamovimento (text), datavalor (text), movimento (text), natureza (text), numero (text), obs (text), valormov (text), valorconta (text), moedamov (text), moedaconta (text)

#### `public.INV_LinhasInventarios` (4,301 rows)
- **Join keys**: `idcabecinventarios`, `id`, `artigo`, `unidade`
- **Value columns**: `precocusto`
- **Quantity columns**: `qtdoriginal`, `qtdstock`, `datastock`
- **Sample columns**: idcabecinventarios (text), id (text), numlinha (text), artigo (text), descricao (text), localizacao (text), lote (text), unidade (text), qtdoriginal (text), qtdstock (text), precocusto (text), observacoes (text)

#### `public.INV_DetalhesLinhasInventarios` (4,301 rows)
- **Join keys**: `id`, `idlinhainventario`, `unidade`
- **Quantity columns**: `estadostock`, `qtdoriginal`, `qtdstock`
- **Sample columns**: id (text), idlinhainventario (text), numlinha (text), estadostock (text), descricao (text), unidade (text), qtdoriginal (text), qtdstock (text)

#### `public.LinhasApuramentoIVA` (113 rows)
- **Join keys**: `idapuramento`
- **Sample columns**: ano (text), tipolancamento (text), periodo (text), numero (text), tipoafectacao (text), diario (text), numdiario (text), descricao (text), foraprazo (text), autorizacaoreembolso (text), apuramento (text), ivapagar (text)

#### `public.AnaliseCustosConfigLinhas` (24 rows)
- **Sample columns**: posto (text), configuracao (text), coluna (text), campo (text), operacao (text), ordem (text), codigo (text)

#### `public.LinhasEncargos` (19 rows)
- **Join keys**: `idcabecencargos`, `id`, `idcabeccompras`, `idlinhascompras`, `artigo`
- **Value columns**: `valor`
- **Sample columns**: idcabecencargos (text), id (text), idcabeccompras (text), idlinhascompras (text), valor (text), versaoultact (text), artigo (text), armazem (text), lote (text)

#### `public.LinhasInternosStatus` (125,477 rows)
- **Join keys**: `idlinha`, `quantidade`
- **Quantity columns**: `quantidade`, `quantcopiada`
- **Sample columns**: idlinha (text), quantidade (text), quantcopiada (text), versaoultact (text)

#### `public.LinhasTesourariaRubricas` (4,396 rows)
- **Join keys**: `id`, `idlinhastesouraria`
- **Value columns**: `valor`
- **Sample columns**: id (text), idlinhastesouraria (text), rubrica (text), valor (text), observacao (text), versaoultact (text)

### Inventory / Warehouse Tables

- `public.INV_Origens` (0 rows) — columns: id (text), idtipoorigem (text), idchave1 (text), idchave2 (text), idchave3 (text), idchave4 (text), numlinha (text), documento (text), data (text), dataintegracao (text), filial (text), idprojecto (text)
- `public.INV_Valorizacoes` (186,593 rows) — columns: id (text), idorigem (text), idmovimentostock (text), idcustopadrao (text), quantidade (text), data (text), datavalor (text), custombase (text), customalt (text), versaoultact (text), valormbase (text), valormalt (text)
- `public.INV_ValoresActuaisCusteio` (2,575 rows) — columns: id (text), artigo (text), grupocustos (text), lote (text), custogrpcstmbase (text), custogrpcstlotmbase (text), custogrpcstmalt (text), custogrpcstlotmalt (text), datacusteio (text), versaoultact (text)
- `public.INV_LinhasTransferenciasArtigo` (337 rows) — columns: id (text), idcabectransferencias (text), numlinha (text), armazem (text), localizacao (text), lote (text), estadostock (text), quantidade (text), precocusto (text), versaoultact (text)
- `public.INV_CabecTransferenciasArtigo` (335 rows) — columns: id (text), tipodoc (text), numdoc (text), filial (text), serie (text), moeda (text), cambio (text), cambiomalt (text), cambiombase (text), arredondamento (text), data (text), observacoes (text)
- `public.INV_LinhasInventarios` (4,301 rows) — columns: idcabecinventarios (text), id (text), numlinha (text), artigo (text), descricao (text), localizacao (text), lote (text), unidade (text), qtdoriginal (text), qtdstock (text), precocusto (text), observacoes (text)
- `public.INV_DetalhesLinhasInventarios` (4,301 rows) — columns: id (text), idlinhainventario (text), numlinha (text), estadostock (text), descricao (text), unidade (text), qtdoriginal (text), qtdstock (text)
- `public.INV_Estados` (7 rows) — columns: estado (text), descricao (text), disponivel (text), existencias (text), inventariavel (text), estadoreserva (text), previsto (text), transito (text), sistema (text), versaoultact (text)
- `public.INV_Custeio` (44,118 rows) — columns: id (text), idorigem (text), tipolancamentocusteio (text), idmovimentostock (text), data (text), dataintegracao (text), numregisto (text), artigo (text), grupocustos (text), lote (text), tipomovimento (text), quantidade (text)
- `public.CNO_Inventario` (6,993 rows) — columns: artigo (text), ano (text), data (text), precoinicial (text), quantidadeinicial (text), precofinal (text), quantidadefinal (text)
- `public.INV_Variacoes` (2,861 rows) — columns: id (text), idcusteioref (text), idcusteiovariacao (text), idvalorizacao (text), dataref (text), datavariacao (text), valormbase (text), valormalt (text), versaoultact (text)

### Cost / Pricing Tables

- `public.FichaCCusto` (15,524 rows) — columns: bem (text), ccusto (text), perc (text), exercicio (text), principal (text), fixa (text), horaimpmanual (text), valorhoraimp (text), periodo (text), projecto (text), wbsitem (text), id (text)
- `public.INV_ValoresActuaisCusteio` (2,575 rows) — columns: id (text), artigo (text), grupocustos (text), lote (text), custogrpcstmbase (text), custogrpcstlotmbase (text), custogrpcstmalt (text), custogrpcstlotmalt (text), datacusteio (text), versaoultact (text)
- `public.AnaliseCustosConfigLinhas` (24 rows) — columns: posto (text), configuracao (text), coluna (text), campo (text), operacao (text), ordem (text), codigo (text)
- `public.INV_Custeio` (44,118 rows) — columns: id (text), idorigem (text), tipolancamentocusteio (text), idmovimentostock (text), data (text), dataintegracao (text), numregisto (text), artigo (text), grupocustos (text), lote (text), tipomovimento (text), quantidade (text)
- `public.AcumuladosCCustoOrigens` (6,614 rows) — columns: ano (text), centro (text), conta (text), moeda (text), mes00cr (text), mes01cr (text), mes02cr (text), mes03cr (text), mes04cr (text), mes05cr (text), mes06cr (text), mes07cr (text)

### Tax/Summary Tables

- `public.ResumoIva` (120,342 rows)
- `public.ResumoIvaLiq` (24,247 rows)
- `public.AcumuladosIVA` (5,618 rows)
- `public.LinhasApuramentoIVA` (113 rows)

## 📌 Table Relevance & Descriptions (analysis files)

- **LinhasDocStatus** (importance 7, medium) — Tracks documentation status of shipments/sales lines; use with `LinhasDoc` and `CabecDoc` for dates/amounts.
- **ResumoIvaLiq** (importance 9, high) — Fiscal calculations for processed products; has `idhistorico` for dating tax entries.
- **ResumoIva** (importance 9, high) — IVA summaries and tax records; use for tax totals/validation.
- **AcumuladosIVA** (importance 9, medium) — Monthly/period IVA accumulation; good for tax rollups.
- **INV_Valorizacoes** (importance 9, medium) — Inventory valuation over time; join with stock movements for cost/valuation analysis.
- **LinhasDocTrans** (importance 8, medium) — Transfer/shipping lines; origin/destination and quantities.
- **CabecDocTaxFree** (importance 8, high) — Tax-free document headers; includes `datanascimento`, tax-free flags.
- **INV_LinhasInventarios** (importance 9, high) — Inventory lines with location/lote/quantities/cost; useful for stock snapshots.
- **LinhasComprasStatus** (importance 9, medium) — Purchase line statuses; quantities and transfer info.
- **FichaCCusto** (importance 8, high) — Cost center allocation/pricing per item; use for cost/margin analysis.

## 🔗 Table Relationships

**Note**: No formal foreign key constraints detected. Use column name matching to find relationships.

## 🎯 Query Workflows by Type

### 1. Monthly Sales Total

**Workflow:**
1. Confirm date column in header table
2. Confirm join path (line → LinhasDoc → CabecDoc if needed)
3. Test join with LIMIT 10
4. Run full query

**Example Query:**
```sql
-- Verify date format
SELECT "data", COUNT(*)
FROM public."CabecDoc"
WHERE "data" IS NOT NULL
GROUP BY "data"
ORDER BY "data" DESC
LIMIT 10;

-- Join test
SELECT hd."data", COUNT(*) AS line_count
FROM public."CabecDoc" hd
JOIN public."LinhasDoc" ld ON hd.id = ld.idcabecdoc
JOIN public."LinhasDocStatus" lds ON ld.id = lds.idlinhasdoc
GROUP BY hd."data"
LIMIT 10;

-- Monthly sales total (September 2025)
SELECT SUM(CAST(ld."precoliquido" AS NUMERIC)) AS total_vendas
FROM public."LinhasDocStatus" lds
JOIN public."LinhasDoc" ld ON lds.idlinhasdoc = ld.id
JOIN public."CabecDoc" hd ON ld.idcabecdoc = hd.id
WHERE EXTRACT(YEAR FROM CAST(hd."data" AS DATE)) = 2025
  AND EXTRACT(MONTH FROM CAST(hd."data" AS DATE)) = 9;
```

**Notes:**
- `data` may be TEXT → CAST/TO_DATE
- `precoliquido` may be TEXT → CAST to NUMERIC
- Multi-step path common: LinhasDocStatus → LinhasDoc → CabecDoc
### 2. Sales by Customer

**Workflow:**
1. Identify customer column (`entidade`/`nome`) in header table
2. Use multi-step join if needed (line → LinhasDoc → CabecDoc)
3. Group by customer and sum value column

**Example Query:**
```sql
-- Find customer columns
SELECT column_name
FROM information_schema.columns
WHERE table_schema = 'public' AND table_name = 'CabecDoc'
  AND (column_name ILIKE '%entidade%' OR column_name ILIKE '%cliente%' OR column_name ILIKE '%nome%');

-- Sales by customer (multi-step join)
SELECT hd.entidade AS cliente, SUM(CAST(ld.precoliquido AS NUMERIC)) AS total_vendas
FROM public.LinhasDocStatus lds
JOIN public.LinhasDoc ld ON lds.idlinhasdoc = ld.id
JOIN public.CabecDoc hd ON ld.idcabecdoc = hd.id
GROUP BY hd.entidade
ORDER BY total_vendas DESC
LIMIT 10;
```

### 3. Sales by Product

```sql
SELECT ld.idartigo AS produto, SUM(CAST(ld.precoliquido AS NUMERIC)) AS total_vendas
FROM public.LinhasDocStatus lds
JOIN public.LinhasDoc ld ON lds.idlinhasdoc = ld.id
JOIN public.CabecDoc hd ON ld.idcabecdoc = hd.id
GROUP BY ld.idartigo
ORDER BY total_vendas DESC
LIMIT 20;
```

### 4. Tax Totals (IVA)

```sql
SELECT SUM(CAST(valor AS NUMERIC)) AS total_iva
FROM public."ResumoIva"
WHERE CAST(idhistorico AS DATE) BETWEEN '2025-09-01' AND '2025-09-30';
```

### 5. Inventory / Stock by Warehouse

```sql
SELECT armazem, SUM(CAST(quantidade AS NUMERIC)) AS stock_total
FROM public."INV_Origens"
GROUP BY armazem
ORDER BY stock_total DESC;
```

### 6. Cost / Valuation

```sql
SELECT AVG(CAST(preco AS NUMERIC)) AS preco_medio, AVG(CAST(custo AS NUMERIC)) AS custo_medio
FROM public."FichaCCusto"
LIMIT 100;
```

### 7. Prediction Prep (export time series)

```sql
SELECT
  CAST(hd.data AS DATE) AS dia,
  SUM(CAST(ld.precoliquido AS NUMERIC)) AS total_vendas
FROM public.LinhasDocStatus lds
JOIN public.LinhasDoc ld ON lds.idlinhasdoc = ld.id
JOIN public.CabecDoc hd ON ld.idcabecdoc = hd.id
GROUP BY dia
ORDER BY dia;
```

Export this result to CSV for forecasting models.

## ⚙️ Execution Rules for the Agent

### Mandatory Steps (NEVER SKIP):

1. Explore first: describe_table, check types, find date/value/join columns.
2. Find relationships: match column names; test joins with LIMIT 10.
3. Handle types: CAST text dates to DATE; CAST text numbers to NUMERIC; test casts.
4. Fallbacks: If a table/column is missing, try alternative names (`CabecDoc%`, `LinhasDoc%`, `idcabecdoc` variants).
5. Performance: Always filter large tables; avoid full scans without WHERE.

### Stop Conditions:
- After 3 structured attempts; report tables/columns tried and errors.

## 📝 Common Query Patterns

### Pattern: Date Format Detection
```sql
SELECT DISTINCT data
FROM public.CabecDoc
WHERE data IS NOT NULL
LIMIT 20;
-- If format is DD/MM/YYYY use TO_DATE(data, 'DD/MM/YYYY')
```
